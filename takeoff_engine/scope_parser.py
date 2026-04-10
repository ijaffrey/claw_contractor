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


def _collect_floor_area(vision_pages: list) -> float | None:
    """Prefer floor area from Vision if available, else None."""
    for p in vision_pages or []:
        fa = p.get("floor_area_sqft") or p.get("total_sqft")
        if isinstance(fa, (int, float)) and fa > 0:
            return float(fa)
    return None


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
) -> dict:
    """Return a scope dict shared across trades + per-trade assessments."""
    job_types = _collect_job_types(permits)
    year = _collect_building_year(vision_pages, permits)
    floor_area = _collect_floor_area(vision_pages)

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
            "n_job_filings": len(permits.get("dob_now_job_filings") or []),
            "n_approved_permits": len(
                permits.get("dob_now_approved_permits") or []
            ),
        },
        "trades": assessments,
    }
