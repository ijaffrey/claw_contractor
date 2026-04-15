"""Chain dob_puller → takeoff_engine → proposal_generator → outreach_engine
for one ranked permit row.
"""

import logging
from pathlib import Path
from typing import Optional

from dob_puller import main as dob_main
from outreach_engine import main as outreach_main
from proposal_generator import main as proposal_main
from takeoff_engine import main as takeoff_main

log = logging.getLogger(__name__)


def run_full_pipeline(
    ranked: dict,
    *,
    contractor: str = "sanz_construction",
    trades: list | None = None,
    use_playwright: bool = True,
) -> dict:
    """Run the full chain for a single ranked permit. Returns artifact paths."""
    if trades is None:
        trades = ["abatement", "concrete", "demo"]

    address = ranked.get("address")
    if not address:
        raise ValueError("ranked permit has no address")

    log.info("=== pipeline: %s (score=%d) ===", address, ranked.get("score", 0))

    artifacts: dict = {
        "address": address,
        "score": ranked.get("score"),
        "job_filing_number": ranked.get("job_filing_number"),
    }

    # Sprint A — run_dob_pull returns the result dict and writes to
    # dob_output/<slug>/result.json on disk.
    slug = _slug(address)
    result_json = Path("dob_output") / slug / "result.json"
    try:
        dob_main.run_dob_pull(address, use_playwright=use_playwright)
        artifacts["result_json"] = str(result_json)
    except Exception as exc:
        log.error("dob_puller failed for %s: %s", address, exc)
        artifacts["dob_puller_error"] = str(exc)
        return artifacts

    if not result_json.exists():
        log.error("Sprint A did not produce result.json at %s", result_json)
        artifacts["dob_puller_error"] = "no result.json produced"
        return artifacts

    # Sprint B
    try:
        takeoff = takeoff_main.run_takeoff(
            input_json=result_json,
            contractor=contractor,
            trades=trades,
            max_pages_per_pdf=2,
        )
        takeoff_path = result_json.parent / "takeoff.json"
        artifacts["takeoff_json"] = str(takeoff_path)
        artifacts["estimated_total_cost"] = (
            takeoff.get("estimated_total_cost") or {}
        ).get("total")
        artifacts["applicable_trades"] = [
            t["name"] for t in takeoff.get("trades", []) if t.get("applicable")
        ]
    except Exception as exc:
        log.error("takeoff_engine failed for %s: %s", address, exc)
        artifacts["takeoff_engine_error"] = str(exc)
        return artifacts

    # Sprint C — proposal
    try:
        proposal_path = proposal_main.run_proposal(
            takeoff_path=Path(takeoff_path),
            contractor=contractor,
        )
        artifacts["proposal_pdf"] = str(proposal_path)
    except Exception as exc:
        log.error("proposal_generator failed for %s: %s", address, exc)
        artifacts["proposal_error"] = str(exc)
        return artifacts

    # Sprint C — outreach
    try:
        contact = _contact_name(ranked)
        result = outreach_main.run_outreach(
            proposal_path=Path(proposal_path),
            contact=contact,
            project=address,
            contractor=contractor,
            takeoff_path=Path(takeoff_path),
        )
        artifacts["drip_schedule"] = result.get("drip_schedule_path")
        artifacts["initial_subject"] = (
            result.get("schedule", {}).get("initial_email", {}).get("subject")
        )
    except Exception as exc:
        log.error("outreach_engine failed for %s: %s", address, exc)
        artifacts["outreach_error"] = str(exc)

    return artifacts


def _contact_name(ranked: dict) -> str:
    owner = (ranked.get("owner_s_business_name") or "").strip()
    if owner:
        return owner
    return "Property Owner"


def _slug(address: str) -> str:
    import re
    s = (address or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")[:80]
