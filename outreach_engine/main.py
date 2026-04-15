"""outreach_engine entry point.

CLI:
    python3 -m outreach_engine.main \\
        --proposal ./proposals/<slug>_proposal.pdf \\
        --contact "Building Manager" \\
        --project "280 Park Avenue renovation"

Optional:
    --takeoff <takeoff.json>   # enrich scope context for the LLM
    --contractor sanz_construction
    --output ./proposals/<slug>_drip_schedule.json
"""

import argparse
import datetime
import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional

from . import claude_client, prompts

log = logging.getLogger("outreach_engine")

CONTRACTOR_PROFILE_ROOT = Path(__file__).resolve().parent.parent / "contractors"


def _setup_logging(verbose: bool = True) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _load_contractor(slug: str) -> dict:
    path = CONTRACTOR_PROFILE_ROOT / f"{slug}.json"
    if not path.exists():
        raise FileNotFoundError(f"Contractor profile not found: {path}")
    with open(path) as fh:
        return json.load(fh)


def _load_takeoff(path: Optional[Path]) -> dict:
    if path is None:
        return {}
    if not Path(path).exists():
        log.warning("Takeoff path does not exist: %s", path)
        return {}
    with open(path) as fh:
        return json.load(fh)


def _scope_summary_for_llm(takeoff: dict) -> str:
    """Build a compact scope summary string for the LLM prompts."""
    if not takeoff:
        return "No takeoff available."
    parts: list = []
    summary = takeoff.get("scope_summary", {}) or {}
    resolved = takeoff.get("resolved", {}) or {}
    if resolved.get("num_floors") and resolved.get("bldg_area_sqft"):
        parts.append(
            f"{int(resolved['num_floors'])}-story, "
            f"{int(resolved['bldg_area_sqft']):,} sqft "
            f"(class {resolved.get('bldg_class','?')}, built {resolved.get('year_built','?')})"
        )
    hvp = summary.get("highest_value_permit") or {}
    if hvp.get("job_description"):
        parts.append(f"job: {hvp['job_description'].strip()[:200]}")
    if hvp.get("work_on_floor"):
        parts.append(str(hvp["work_on_floor"]).strip())
    applicable = [t["name"] for t in takeoff.get("trades", []) if t.get("applicable")]
    if applicable:
        parts.append("trades: " + ", ".join(applicable))
    total = (takeoff.get("estimated_total_cost") or {}).get("total")
    if total:
        parts.append(f"estimated total ${total:,.0f}")
    return " | ".join(parts) if parts else "Scope details available in attached proposal."


def _job_number(takeoff: dict) -> str:
    hvp = (takeoff.get("scope_summary") or {}).get("highest_value_permit") or {}
    return hvp.get("job_filing_number") or "(see proposal)"


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        # Try a minor repair: unescape or strip trailing commas
        fixed = re.sub(r",\s*([}\]])", r"\1", m.group(0))
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            return {}


def generate_initial_email(
    *,
    contractor: dict,
    contact: str,
    project: str,
    takeoff: dict,
) -> dict:
    prompt = prompts.INITIAL_EMAIL_PROMPT.format(
        contractor_name=contractor.get("name", ""),
        contact=contact,
        project=project,
        job_number=_job_number(takeoff),
        scope_summary=_scope_summary_for_llm(takeoff),
        sender=contractor.get("contact", ""),
        sender_title="Principal",
    )
    text = claude_client.generate_text(prompt, system=prompts.OUTREACH_SYSTEM)
    data = _extract_json(text)
    if not data.get("subject") or not data.get("body"):
        log.warning("Initial email LLM output missing fields; using raw")
        data = {"subject": f"Proposal for {project}", "body": text}
    return {
        "subject": data["subject"],
        "body": data["body"],
        "send_date": "today",
    }


def generate_followup(
    step: dict,
    *,
    contractor: dict,
    contact: str,
    project: str,
    takeoff: dict,
) -> dict:
    prompt = prompts.DRIP_PROMPT.format(
        day_label=step["day_label"],
        seq=step["seq"],
        contractor_name=contractor.get("name", ""),
        contact=contact,
        project=project,
        job_number=_job_number(takeoff),
        scope_summary=_scope_summary_for_llm(takeoff),
        sender=contractor.get("contact", ""),
        purpose=step["purpose"],
        extra_rules=step["extra_rules"],
    )
    text = claude_client.generate_text(prompt, system=prompts.OUTREACH_SYSTEM)
    data = _extract_json(text)
    if not data.get("subject") or not data.get("body"):
        log.warning("Day-%d LLM output missing fields; using raw", step["day"])
        data = {"subject": f"Follow-up: {project}", "body": text}
    return {
        "day": step["day"],
        "subject": data["subject"],
        "body": data["body"],
        "channel": "email",
    }


def build_drip_schedule(
    *,
    contractor: dict,
    contact: str,
    project: str,
    proposal_path: Path,
    takeoff: dict,
) -> dict:
    log.info("Generating initial outreach email for %s", contact)
    initial = generate_initial_email(
        contractor=contractor, contact=contact, project=project, takeoff=takeoff
    )
    followups: list = []
    for step in prompts.DRIP_STEPS:
        log.info("Generating day-%d follow-up", step["day"])
        followups.append(
            generate_followup(
                step,
                contractor=contractor,
                contact=contact,
                project=project,
                takeoff=takeoff,
            )
        )

    return {
        "schema_version": "1.0",
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "contractor": contractor.get("name", ""),
        "contact": contact,
        "project": project,
        "proposal_pdf": str(proposal_path),
        "initial_email": initial,
        "followups": followups,
    }


def _derive_output_path(proposal_path: Path, explicit: Optional[Path]) -> Path:
    if explicit:
        return explicit
    return proposal_path.parent / (proposal_path.stem + "_drip_schedule.json")


def _derive_takeoff_path(proposal_path: Path, explicit: Optional[Path]) -> Path | None:
    """Guess the takeoff.json location if not explicitly given."""
    if explicit:
        return explicit
    # Convention: proposals/<slug>_<contractor>_proposal.pdf
    # Takeoffs:    dob_output/<slug>/takeoff.json
    name = proposal_path.stem  # "<slug>_<contractor>_proposal"
    for suffix in ("_sanz_construction_proposal", "_proposal"):
        if name.endswith(suffix):
            slug = name[: -len(suffix)]
            candidate = Path("dob_output") / slug / "takeoff.json"
            if candidate.exists():
                return candidate
    return None


def run_outreach(
    *,
    proposal_path: Path,
    contact: str,
    project: str,
    contractor: str = "sanz_construction",
    takeoff_path: Path | None = None,
    output_path: Path | None = None,
) -> dict:
    proposal_path = Path(proposal_path)
    profile = _load_contractor(contractor)
    takeoff = _load_takeoff(_derive_takeoff_path(proposal_path, takeoff_path))

    schedule = build_drip_schedule(
        contractor=profile,
        contact=contact,
        project=project,
        proposal_path=proposal_path,
        takeoff=takeoff,
    )
    out = _derive_output_path(proposal_path, output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        json.dump(schedule, fh, indent=2)
    log.info("Wrote drip schedule to %s", out)
    return {"drip_schedule_path": str(out), "schedule": schedule}


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="outreach_engine",
        description="Generate initial email + drip follow-ups for a proposal.",
    )
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--contact", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--contractor", default="sanz_construction")
    parser.add_argument("--takeoff", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    _setup_logging(verbose=not args.quiet)
    try:
        result = run_outreach(
            proposal_path=Path(args.proposal),
            contact=args.contact,
            project=args.project,
            contractor=args.contractor,
            takeoff_path=Path(args.takeoff) if args.takeoff else None,
            output_path=Path(args.output) if args.output else None,
        )
    except Exception as exc:
        log.exception("outreach_engine failed: %s", exc)
        return 2

    s = result["schedule"]
    summary = {
        "drip_schedule_path": result["drip_schedule_path"],
        "contact": s["contact"],
        "project": s["project"],
        "initial_subject": s["initial_email"]["subject"],
        "followup_count": len(s["followups"]),
        "followup_days": [f["day"] for f in s["followups"]],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
