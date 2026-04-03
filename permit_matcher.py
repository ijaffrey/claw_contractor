"""
Permit Matcher — matches general contractors with subcontractors.

Scoring is based on:
  - Permit type compatibility (e.g. GC on a plumbing permit → plumbing subs)
  - Project scope similarity (estimated cost bracket)
  - Location proximity (same borough or adjacent)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Permit type → relevant sub trades
PERMIT_TRADE_MAP = {
    "NB": ["general", "plumbing", "electrical", "hvac", "steel", "concrete", "excavation"],
    "A1": ["general", "plumbing", "electrical", "hvac", "carpentry", "drywall"],
    "A2": ["general", "plumbing", "electrical", "carpentry"],
    "A3": ["general", "carpentry", "drywall", "painting"],
    "DM": ["general", "demolition", "excavation", "environmental"],
    "PL": ["plumbing", "fire_suppression"],
    "EL": ["electrical", "low_voltage", "fire_alarm"],
    "EW": ["electrical"],
    "FO": ["foundation", "excavation", "concrete", "steel"],
    "SD": ["general", "scaffolding"],
    "SG": ["signage", "electrical"],
    "FP": ["fire_suppression", "plumbing"],
    "MH": ["mechanical", "hvac"],
    "OT": ["general"],
    # DOB NOW filing reasons
    "INITIAL PERMIT": ["general", "plumbing", "electrical", "hvac"],
    "RENEWAL": ["general"],
    "POST APPROVAL AMENDMENT": ["general"],
}

# Adjacent borough pairs (for location proximity scoring)
ADJACENT_BOROUGHS = {
    "Manhattan": {"Bronx", "Brooklyn", "Queens"},
    "Bronx": {"Manhattan", "Queens"},
    "Brooklyn": {"Manhattan", "Queens", "Staten Island"},
    "Queens": {"Manhattan", "Bronx", "Brooklyn"},
    "Staten Island": {"Brooklyn"},
}

# Cost brackets for scope matching
COST_BRACKETS = [
    (0, 50_000, "small"),
    (50_000, 250_000, "medium"),
    (250_000, 1_000_000, "large"),
    (1_000_000, 10_000_000, "major"),
    (10_000_000, float("inf"), "mega"),
]


def get_cost_bracket(cost: Optional[float]) -> str:
    """Return the cost bracket label for a given estimated cost."""
    if not cost or cost <= 0:
        return "unknown"
    for low, high, label in COST_BRACKETS:
        if low <= cost < high:
            return label
    return "mega"


def get_relevant_trades(permit_type: Optional[str]) -> list:
    """Get relevant sub-trades for a permit type."""
    if not permit_type:
        return ["general"]
    key = permit_type.strip().upper()
    return PERMIT_TRADE_MAP.get(key, ["general"])


def score_match(gc_profile: dict, sub_profile: dict, permit: dict) -> dict:
    """
    Score how well a subcontractor matches a GC's permit.

    Returns:
        Dict with match_score (0-100), individual scores, and reasons.
    """
    reasons = []
    scores = {"permit_type": 0, "scope": 0, "location": 0}

    # --- Permit type match (0-40 points) ---
    permit_type = permit.get("permit_type", "")
    relevant_trades = get_relevant_trades(permit_type)
    sub_trades = sub_profile.get("trade_types", []) or []

    trade_overlap = set(t.lower() for t in sub_trades) & set(t.lower() for t in relevant_trades)
    if trade_overlap:
        scores["permit_type"] = min(40, len(trade_overlap) * 20)
        reasons.append(f"Trade match: {', '.join(trade_overlap)}")

    # --- Scope match (0-30 points) ---
    permit_cost = permit.get("estimated_job_cost")
    gc_avg_cost = gc_profile.get("avg_project_cost")
    sub_avg_cost = sub_profile.get("avg_project_cost")

    permit_bracket = get_cost_bracket(permit_cost)
    sub_bracket = get_cost_bracket(sub_avg_cost)

    if permit_bracket != "unknown" and sub_bracket != "unknown":
        if permit_bracket == sub_bracket:
            scores["scope"] = 30
            reasons.append(f"Same cost bracket: {permit_bracket}")
        else:
            # Adjacent bracket gets partial credit
            bracket_labels = [b[2] for b in COST_BRACKETS]
            try:
                pi = bracket_labels.index(permit_bracket)
                si = bracket_labels.index(sub_bracket)
                if abs(pi - si) == 1:
                    scores["scope"] = 15
                    reasons.append(f"Adjacent cost bracket: permit={permit_bracket}, sub={sub_bracket}")
            except ValueError:
                pass
    elif permit_bracket == "unknown" and sub_bracket == "unknown":
        scores["scope"] = 10  # Both unknown, slight default
        reasons.append("Cost data unavailable for both")

    # --- Location match (0-30 points) ---
    permit_borough = permit.get("borough", "")
    sub_boroughs = sub_profile.get("boroughs_active", []) or []

    if permit_borough and sub_boroughs:
        if permit_borough in sub_boroughs:
            scores["location"] = 30
            reasons.append(f"Same borough: {permit_borough}")
        else:
            adjacent = ADJACENT_BOROUGHS.get(permit_borough, set())
            if adjacent & set(sub_boroughs):
                scores["location"] = 15
                overlap = adjacent & set(sub_boroughs)
                reasons.append(f"Adjacent borough: sub active in {', '.join(overlap)}")

    total = sum(scores.values())

    return {
        "match_score": total,
        "permit_type_match": scores["permit_type"] > 0,
        "scope_match": scores["scope"] > 0,
        "location_match": scores["location"] > 0,
        "match_reasons": reasons,
        "score_breakdown": scores,
    }


def find_matches(permit: dict, gc_profile: dict,
                 sub_profiles: list, min_score: int = 30) -> list:
    """
    Find matching subcontractors for a GC's permit.

    Args:
        permit: Normalized permit dict.
        gc_profile: The general contractor's profile dict.
        sub_profiles: List of subcontractor profile dicts to evaluate.
        min_score: Minimum match score to include (0-100).

    Returns:
        List of match dicts sorted by score descending.
    """
    matches = []

    for sub in sub_profiles:
        # Don't match a contractor with itself
        sub_id = sub.get("id")
        gc_id = gc_profile.get("id")
        if sub_id and gc_id and sub_id == gc_id:
            continue
        sub_lic = sub.get("license_number", "")
        gc_lic = gc_profile.get("license_number", "")
        if sub_lic and gc_lic and sub_lic == gc_lic:
            continue

        result = score_match(gc_profile, sub, permit)
        if result["match_score"] >= min_score:
            matches.append({
                "gc_profile_id": gc_profile.get("id"),
                "sub_profile_id": sub.get("id"),
                "permit_id": permit.get("id"),
                **result,
            })

    matches.sort(key=lambda m: m["match_score"], reverse=True)
    return matches
