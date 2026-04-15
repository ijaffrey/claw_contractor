"""Parse Vision output + Sprint A permit metadata into per-trade scope.

Produces a {trade: {applicable, reasons, evidence, keywords_hit, year,
job_types, floor_area_sqft_estimate, confidence}} mapping that the
quantity_estimator then turns into priced line items.
"""

import logging
import re
from typing import Iterable

log = logging.getLogger(__name__)

TRADE_KEYWORDS = {
    "abatement": [
        "gut",
        "full demo",
        "asbestos",
        "acm",
        "lbp",
        "lead paint",
        "hazardous",
        "abatement",
    ],
    "concrete": [
        "slab",
        "pour",
        "foundation",
        "footing",
        "core drill",
        "patch",
        "concrete",
    ],
    "roofing": [
        "roof",
        "membrane",
        "parapet",
        "flashing",
        "tpo",
        "epdm",
    ],
    "demo": [
        "demolish",
        "demolition",
        "remove",
        "gut",
        "strip",
    ],
    "sitework": [
        "excavation",
        "grading",
        "site prep",
        "site-work",
        "sitework",
    ],
}

TRADE_JOB_TYPES = {
    "demo": {"DM", "A1"},
    "sitework": {"NB"},
}

ABATEMENT_YEAR_CUTOFF = 1980


def _permit_text_blob(permits: dict) -> str:
    """Concatenate every text-ish field from Sprint A permits for keyword search."""
    chunks: list = []
    for source in ("dob_now_job_filings", "dob_now_approved_permits"):
        for row in (permits.get(source) or []):
            for v in row.values():
                if isinstance(v, str):
                    chunks.append(v)
    for j in permits.get("bis_jobs") or []:
        for v in j.values():
            if isinstance(v, str):
                chunks.append(v)
    return " ".join(chunks).lower()


def _collect_job_types(permits: dict) -> set:
    out: set = set()
    for row in (permits.get("dob_now_job_filings") or []):
        jt = row.get("job_type")
        if jt:
            out.add(str(jt).upper())
    return out


def _collect_floor_area_from_vision(vision_pages: list) -> float | None:
    """Prefer floor area from Vision extractions if available."""
    for p in vision_pages or []:
        fa = p.get("floor_area_sqft") or p.get("total_sqft")
        if isinstance(fa, (int, float)) and fa > 0:
            return float(fa)
    return None


def _permit_reported_floor_area(permits: dict) -> tuple[float | None, dict | None]:
    """Scan DOB NOW Build Approved Permit Applications (w9ak-ipjd) for the
    single filing with the largest total_construction_floor_area > 0.

    Returns (sqft, source_row) or (None, None).
    """
    best_area = 0.0
    best_row: dict | None = None
    for row in (permits.get("dob_now_build_approved_apps") or []):
        raw = row.get("total_construction_floor_area")
        try:
            area = float(raw) if raw not in (None, "") else 0.0
        except (TypeError, ValueError):
            continue
        if area > best_area:
            best_area = area
            best_row = row
    if best_area > 0 and best_row is not None:
        return best_area, {
            "job_filing_number": best_row.get("job_filing_number"),
            "job_type": best_row.get("job_type"),
            "initial_cost_usd": _to_float(best_row.get("initial_cost")),
            "work_on_floor": best_row.get("work_on_floor"),
            "filing_date": best_row.get("filing_date"),
            "approved_date": best_row.get("approved_date"),
            "total_construction_floor_area_sqft": best_area,
        }
    return None, None


def _to_float(v) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _highest_value_permit(permits: dict) -> dict | None:
    """Scan approved_permits for the highest estimated_job_costs entry.

    Used as a proxy for "most significant job at this address".
    """
    best: dict | None = None
    best_cost = -1.0
    for p in (permits.get("dob_now_approved_permits") or []):
        raw = p.get("estimated_job_costs")
        try:
            cost = float(raw) if raw not in (None, "") else 0.0
        except (TypeError, ValueError):
            continue
        if cost > best_cost:
            best_cost = cost
            best = p
    if best is None or best_cost <= 0:
        return None
    return {
        "estimated_job_costs_usd": best_cost,
        "work_type": best.get("work_type"),
        "job_filing_number": best.get("job_filing_number"),
        "work_on_floor": best.get("work_on_floor"),
        "job_description": best.get("job_description"),
        "approved_date": best.get("approved_date"),
        "permit_status": best.get("permit_status"),
    }


def _resolved_building_metrics(resolved: dict | None) -> dict:
    """Extract PLUTO building metrics + derived typical floor plate."""
    resolved = resolved or {}
    bldg_area = resolved.get("bldg_area_sqft")
    num_floors = resolved.get("num_floors")
    typical_floor = None
    if (
        isinstance(bldg_area, (int, float)) and bldg_area > 0
        and isinstance(num_floors, (int, float)) and num_floors > 0
    ):
        typical_floor = round(bldg_area / num_floors, 2)
    return {
        "bldg_area_sqft": bldg_area,
        "num_floors": num_floors,
        "year_built": resolved.get("year_built"),
        "bldg_class": resolved.get("bldg_class"),
        "typical_floor_plate_sqft": typical_floor,
    }


def _collect_building_year(vision_pages: list, permits: dict) -> int | None:
    for p in vision_pages or []:
        y = p.get("building_year")
        if isinstance(y, (int, float)) and 1700 < y < 2100:
            return int(y)
    # Fall back to any year-looking string in permit rows
    blob = _permit_text_blob(permits)
    m = re.search(r"\b(17|18|19|20)\d{2}\b", blob)
    if m:
        return int(m.group(0))
    return None


def _vision_keyword_hits(vision_pages: list, keywords: Iterable[str]) -> list:
    hits: list = []
    for p in vision_pages or []:
        for k, v in p.items():
            if isinstance(v, str):
                low = v.lower()
                for kw in keywords:
                    if kw in low and kw not in hits:
                        hits.append(kw)
    return hits


def assess_trade(
    trade: str,
    *,
    permits: dict,
    vision_pages: list,
    job_types: set,
    year: int | None,
) -> dict:
    """Decide if a trade is applicable and why."""
    blob = _permit_text_blob(permits)
    kws = TRADE_KEYWORDS.get(trade, [])
    perm_hits = [k for k in kws if k in blob]
    vision_hits = _vision_keyword_hits(vision_pages, kws)
    all_hits = sorted(set(perm_hits + vision_hits))

    reasons: list = []
    applicable = False

    if trade == "abatement":
        if year is not None and year < ABATEMENT_YEAR_CUTOFF:
            reasons.append(f"building_year={year} (< {ABATEMENT_YEAR_CUTOFF})")
            applicable = True
        if all_hits:
            reasons.append(f"keywords={all_hits}")
            applicable = True

    elif trade in TRADE_JOB_TYPES:
        required = TRADE_JOB_TYPES[trade]
        jt_match = job_types & required
        if jt_match:
            reasons.append(f"job_type in {sorted(required)} found: {sorted(jt_match)}")
            applicable = True
        if all_hits:
            reasons.append(f"keywords={all_hits}")
            applicable = True

    else:
        if all_hits:
            reasons.append(f"keywords={all_hits}")
            applicable = True

    confidence = "low"
    if applicable:
        if perm_hits and vision_hits:
            confidence = "high"
        elif perm_hits or vision_hits:
            confidence = "medium"

    return {
        "trade": trade,
        "applicable": applicable,
        "reasons": reasons,
        "keywords_hit": all_hits,
        "permit_keyword_hits": perm_hits,
        "vision_keyword_hits": vision_hits,
        "confidence": confidence,
    }


def build_scope(
    trades: list,
    *,
    permits: dict,
    vision_pages: list,
    resolved: dict | None = None,
) -> dict:
    """Return a scope dict shared across trades + per-trade assessments."""
    job_types = _collect_job_types(permits)

    vision_year = None
    for p in (vision_pages or []):
        y = p.get("building_year")
        if isinstance(y, (int, float)) and 1700 < y < 2100:
            vision_year = int(y)
            break

    bldg = _resolved_building_metrics(resolved)

    # Year precedence: PLUTO yearbuilt > Vision > permit text regex fallback
    year = bldg.get("year_built") or vision_year or _collect_building_year(
        vision_pages, permits
    )

    # Floor area precedence:
    #   1. Permit-reported total_construction_floor_area (w9ak-ipjd)
    #   2. PLUTO typical_floor_plate (bldgarea / numfloors)
    #   3. Vision-extracted floor_area
    #   4. None (quantity_estimator supplies a 1000 sqft default)
    permit_area, permit_area_row = _permit_reported_floor_area(permits)
    vision_fa = _collect_floor_area_from_vision(vision_pages)
    if permit_area:
        floor_area = permit_area
        floor_area_source = "permit_total_construction_floor_area"
    elif bldg.get("typical_floor_plate_sqft"):
        floor_area = bldg["typical_floor_plate_sqft"]
        floor_area_source = "pluto_typical_floor_plate"
    elif vision_fa:
        floor_area = vision_fa
        floor_area_source = "vision_extraction"
    else:
        floor_area = None
        floor_area_source = None

    best_permit = _highest_value_permit(permits)

    assessments = {}
    for t in trades:
        assessments[t] = assess_trade(
            t,
            permits=permits,
            vision_pages=vision_pages,
            job_types=job_types,
            year=year,
        )

    return {
        "shared": {
            "job_types": sorted(job_types),
            "building_year": year,
            "floor_area_sqft_estimate": floor_area,
            "floor_area_source": floor_area_source,
            "permit_floor_area_row": permit_area_row,
            "bldg_area_sqft_total": bldg.get("bldg_area_sqft"),
            "num_floors": bldg.get("num_floors"),
            "bldg_class": bldg.get("bldg_class"),
            "highest_value_permit": best_permit,
            "n_job_filings": len(permits.get("dob_now_job_filings") or []),
            "n_approved_permits": len(
                permits.get("dob_now_approved_permits") or []
            ),
            "n_build_approved_apps": len(
                permits.get("dob_now_build_approved_apps") or []
            ),
        },
        "trades": assessments,
    }
