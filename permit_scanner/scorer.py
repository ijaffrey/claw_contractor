"""Sanz-fit scoring for DOB permits.

Scoring rules (per Sprint D brief):
  +30 if building year < 1980 (abatement trigger)
  +20 if job_type is DM or A1 (larger scope)
  +20 if estimated_job_cost > $500,000
  +15 if no GC name on file (owner-filed = open position)
  +15 if trades match abatement/concrete/demo keywords in description
Max: 100
"""

import logging
import re
from typing import Optional

from .socrata import JOB_TYPE_CODE

log = logging.getLogger(__name__)

ABATEMENT_YEAR_CUTOFF = 1980
LARGE_SCOPE_COST_CUTOFF = 500_000
TRADE_KEYWORDS = (
    "asbestos",
    "acm",
    "lbp",
    "lead",
    "abatement",
    "hazardous",
    "concrete",
    "slab",
    "foundation",
    "demolish",
    "demolition",
    "gut",
    "strip out",
    "interior demo",
)

# Common DOB filing representative / licensed contractor business names that
# signal a GC is already engaged. If the applicant / permittee business name
# looks like an LLC/Inc that is NOT the owner, we treat that as "GC on file".
OWNER_SUFFIXES = ("LLC", "INC", "CORP", "ASSOCIATES", "TRUST", "PROPERTIES", "REALTY", "COMPANY", "CO", "PARTNERS")


def _num(v) -> Optional[float]:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _has_gc_on_file(permit: dict) -> bool:
    """True if a licensed GC appears to be named in the filing.

    w9ak-ipjd carries applicant first/last name and a filing representative
    business name. If EITHER is populated with a non-owner name, we count
    that as "GC on file". The heuristic is: if applicant_last_name is
    present, someone is formally filing on behalf of the owner → GC on file.
    """
    applicant_last = (permit.get("applicant_last_name") or "").strip()
    applicant_first = (permit.get("applicant_first_name") or "").strip()
    filing_rep_biz = (permit.get("filing_representative_business_name") or "").strip()
    if applicant_last or applicant_first:
        return True
    if filing_rep_biz:
        return True
    return False


def _description_blob(permit: dict) -> str:
    """Build a searchable text blob from every work_type_ field on the row."""
    parts: list = []
    for k, v in permit.items():
        if not isinstance(v, str):
            continue
        kl = k.lower()
        if (
            "work_type" in kl
            or kl in ("job_description", "building_type", "owner_s_business_name")
        ):
            parts.append(v)
    return " ".join(parts).lower()


def _matches_trade_keywords(permit: dict) -> list:
    blob = _description_blob(permit)
    return [k for k in TRADE_KEYWORDS if k in blob]


def _job_type_code(permit: dict) -> str:
    raw = permit.get("job_type") or ""
    return JOB_TYPE_CODE.get(raw, raw.upper().replace(" ", "_"))


def score_permit(permit: dict, *, pluto_by_bbl: dict) -> dict:
    """Score a single permit and return the enriched record."""
    reasons: list = []
    score = 0

    # Lookup PLUTO year if available
    bbl_key = str(permit.get("bbl", "")).split(".")[0]
    pluto = pluto_by_bbl.get(bbl_key, {}) if pluto_by_bbl else {}
    year = pluto.get("year_built")

    if year is not None and year < ABATEMENT_YEAR_CUTOFF:
        score += 30
        reasons.append(f"+30 year_built={year} (< {ABATEMENT_YEAR_CUTOFF})")

    code = _job_type_code(permit)
    if code in ("DM", "A1_A2"):
        score += 20
        reasons.append(f"+20 job_type={permit.get('job_type')} (DM/A1-equiv)")

    cost = _num(permit.get("initial_cost"))
    if cost is not None and cost > LARGE_SCOPE_COST_CUTOFF:
        score += 20
        reasons.append(f"+20 initial_cost=${cost:,.0f} (> ${LARGE_SCOPE_COST_CUTOFF:,})")

    if not _has_gc_on_file(permit):
        score += 15
        reasons.append("+15 no GC / filing rep on file (owner-filed)")

    kw_hits = _matches_trade_keywords(permit)
    if kw_hits:
        score += 15
        reasons.append(f"+15 trade keywords: {kw_hits[:5]}")

    return {
        "score": score,
        "scoring_reasons": reasons,
        "job_filing_number": permit.get("job_filing_number"),
        "job_type": permit.get("job_type"),
        "job_type_code": code,
        "address": _address(permit),
        "house_no": permit.get("house_no"),
        "street_name": permit.get("street_name"),
        "borough": permit.get("borough"),
        "bin": permit.get("bin"),
        "bbl": bbl_key or permit.get("bbl"),
        "initial_cost_usd": cost,
        "total_construction_floor_area_sqft": _num(
            permit.get("total_construction_floor_area")
        ),
        "owner_s_business_name": permit.get("owner_s_business_name"),
        "filing_date": permit.get("filing_date"),
        "approved_date": permit.get("approved_date"),
        "year_built": year,
        "bldg_area_sqft": pluto.get("bldg_area_sqft"),
        "num_floors": pluto.get("num_floors"),
        "trade_keyword_hits": kw_hits,
        "raw_permit_keys": sorted(k for k in permit.keys() if permit[k] not in (None, "", 0)),
    }


def _address(permit: dict) -> str:
    hn = (permit.get("house_no") or "").strip()
    st = re.sub(r"\s+", " ", (permit.get("street_name") or "")).strip().title()
    bor = (permit.get("borough") or "").title()
    if hn and st:
        return f"{hn} {st}, {bor}".strip(", ")
    return bor or "(unknown address)"


SCORE_BUCKETS = [
    (80, 100, "80-100 (hot)"),
    (65, 79, "65-79 (strong)"),
    (50, 64, "50-64 (qualify)"),
    (35, 49, "35-49 (marginal)"),
    (0, 34, "0-34 (skip)"),
]


def bucket_label(score: int) -> str:
    for lo, hi, label in SCORE_BUCKETS:
        if lo <= score <= hi:
            return label
    return "unknown"


def bucket_breakdown(scored: list) -> dict:
    """Return aggregated stats per score bucket for a list of scored permits."""
    out: list = []
    for lo, hi, label in SCORE_BUCKETS:
        members = [s for s in scored if lo <= s["score"] <= hi]
        costs = [s["initial_cost_usd"] for s in members if s.get("initial_cost_usd")]
        total_cost = sum(costs) if costs else 0.0
        out.append(
            {
                "bucket": label,
                "min_score": lo,
                "max_score": hi,
                "count": len(members),
                "pct": None,  # filled in by caller
                "total_initial_cost_usd": total_cost,
                "avg_initial_cost_usd": (total_cost / len(costs)) if costs else 0.0,
            }
        )
    total = sum(b["count"] for b in out) or 1
    for b in out:
        b["pct"] = round(100.0 * b["count"] / total, 1)
    return {"total_scored": sum(b["count"] for b in out), "buckets": out}


def score_all(permits: list, *, pluto_by_bbl: dict) -> list:
    """Score every permit (no filtering, no dedupe) — used for bucket stats."""
    return [score_permit(p, pluto_by_bbl=pluto_by_bbl) for p in permits]


def rank_permits(
    permits: list,
    *,
    pluto_by_bbl: dict,
    min_score: int = 50,
    top_n: int = 20,
    dedupe_by_bin: bool = True,
) -> list:
    """Score all permits, dedupe by BIN (keep highest score), filter and sort."""
    scored = [score_permit(p, pluto_by_bbl=pluto_by_bbl) for p in permits]

    if dedupe_by_bin:
        best_by_bin: dict = {}
        for s in scored:
            b = s.get("bin") or s.get("bbl") or s.get("job_filing_number")
            if not b:
                continue
            cur = best_by_bin.get(b)
            if cur is None or s["score"] > cur["score"]:
                best_by_bin[b] = s
        scored = list(best_by_bin.values())

    filtered = [s for s in scored if s["score"] >= min_score]
    filtered.sort(key=lambda x: (-x["score"], -(x.get("initial_cost_usd") or 0)))
    return filtered[:top_n]
