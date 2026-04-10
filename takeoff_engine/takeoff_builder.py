"""Assemble the final takeoff.json output."""

import datetime
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def build_takeoff(
    *,
    sprint_a_result: dict,
    contractor: str,
    trades: list,
    classifications: list,
    vision_pages: list,
    scope: dict,
    priced: dict,
) -> dict:
    """Assemble the final takeoff dict."""
    shared = scope.get("shared", {})
    trades_list = []
    for trade in trades:
        t = priced["per_trade"].get(trade, {})
        trades_list.append(
            {
                "name": trade,
                "applicable": t.get("applicable", False),
                "confidence": t.get("confidence", "low"),
                "reasons": t.get("reasons", []),
                "keywords_hit": t.get("keywords_hit", []),
                "line_items": t.get("line_items", []),
                "pricing": t.get("pricing", {}),
            }
        )

    scope_summary = {
        "building_year": shared.get("building_year"),
        "floor_area_sqft_estimate": shared.get("floor_area_sqft_estimate"),
        "job_types": shared.get("job_types", []),
        "n_job_filings": shared.get("n_job_filings", 0),
        "n_approved_permits": shared.get("n_approved_permits", 0),
        "n_pages_classified": len(classifications or []),
        "n_pages_extracted": len(vision_pages or []),
    }

    return {
        "schema_version": "1.0",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "contractor": contractor,
        "input_address": sprint_a_result.get("input_address"),
        "resolved": sprint_a_result.get("resolved", {}),
        "trades": trades_list,
        "scope_summary": scope_summary,
        "classifications": classifications,
        "vision_extractions": vision_pages,
        "flags": priced.get("flags", []),
        "estimated_total_cost": priced.get("grand_total", {}),
    }


def write_takeoff(takeoff: dict, out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(takeoff, fh, indent=2, default=str)
    log.info("Wrote takeoff to %s", out_path)
    return out_path
