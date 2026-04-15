"""Produce the plain-English scope-of-work paragraph for a proposal.

Deliberately rule-based (no LLM) so that the proposal PDF is 100%
deterministic given the takeoff input. The outreach_engine is where
Claude does the writing.
"""

import logging

log = logging.getLogger(__name__)

TRADE_DESCRIPTIONS = {
    "abatement": "hazardous-material abatement (floor tile, ceiling tile, pipe insulation, and ACM disposal as required)",
    "concrete": "concrete work (slab patching, core drilling, and new pours as required)",
    "roofing": "roofing (membrane, tear-off, and flashing as required)",
    "demo": "interior demolition and debris removal",
    "sitework": "site preparation (excavation and grading)",
}


def _address_line(takeoff: dict) -> str:
    addr = takeoff.get("input_address") or "the project address"
    resolved = takeoff.get("resolved", {}) or {}
    parts = [addr]
    if resolved.get("num_floors"):
        parts.append(f"{int(resolved['num_floors'])}-story building")
    if resolved.get("bldg_class"):
        parts.append(f"class {resolved['bldg_class']}")
    return ", ".join(parts)


def build_scope_paragraph(takeoff: dict) -> str:
    """Return a 2-3 sentence plain-English scope statement."""
    applicable = [t for t in takeoff.get("trades", []) if t.get("applicable")]
    if not applicable:
        return (
            "Sanz Construction proposes to review the referenced project and "
            "provide a detailed scope once drawings and site access are made "
            "available."
        )

    lines = []
    lines.append(
        f"Sanz Construction proposes to perform the work described below at "
        f"{_address_line(takeoff)}."
    )

    summary = takeoff.get("scope_summary", {}) or {}
    hvp = summary.get("highest_value_permit") or {}
    if hvp.get("job_description"):
        lines.append(
            f"Work references job filing {hvp.get('job_filing_number','(unknown)')}: "
            f"{hvp['job_description'].strip()}"
        )
    elif summary.get("floor_area_sqft_estimate"):
        lines.append(
            f"Scope area is based on a typical floor plate of "
            f"{int(summary['floor_area_sqft_estimate']):,} sqft."
        )

    trade_descs = [
        TRADE_DESCRIPTIONS.get(t["name"], t["name"]) for t in applicable
    ]
    if len(trade_descs) == 1:
        trade_text = trade_descs[0]
    elif len(trade_descs) == 2:
        trade_text = " and ".join(trade_descs)
    else:
        trade_text = ", ".join(trade_descs[:-1]) + ", and " + trade_descs[-1]
    lines.append(f"Trades included in this proposal: {trade_text}.")

    return " ".join(lines)


EXCLUSIONS = [
    "Mechanical, electrical, and plumbing (MEP) work",
    "Permit and DOB filing fees",
    "Engineering, architectural, and design services",
    "Asbestos/lead survey and testing (abatement is based on assumed conditions)",
    "Hazardous material disposal beyond what is explicitly quantified",
    "Temporary protection of adjacent occupied spaces",
    "After-hours and overtime premium labor",
    "Utility hookups and service upgrades",
    "Finish-out work (painting, flooring, ceilings) unless explicitly listed",
]
