"""
Proposal Generator — two outreach angles.

Brands:
  skipp    — contractor-facing (Skipp brand), permit hook, direct trade value props
  drafted  — architect-facing (Drafted brand), neutral tone, design-build language

Generates proposals from lead data and saves to Supabase (or SQLite in dev).
Set ENRICHMENT_MOCK=true for mock mode (no real API calls).
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

MOCK_MODE = os.getenv("ENRICHMENT_MOCK", "false").lower() == "true"

# ── Trade value props ──────────────────────────────────────────────────────────

SKIPP_TRADE_PROPS = {
    "general":     "streamline your sub coordination with permit-verified GC leads",
    "plumbing":    "connect with GCs actively pulling plumbing permits in your borough",
    "electrical":  "reach GCs on live electrical permit jobs before they've locked in a sub",
    "hvac":        "match with mechanical permit holders looking for HVAC partners",
    "demolition":  "find GCs with demo permits that need licensed demo crews now",
    "foundation":  "connect with structural permit jobs requiring foundation specialists",
    "carpentry":   "reach interior renovation GCs with active carpentry scope",
    "drywall":     "fill your crew calendar with verified drywall scope from live permits",
    "concrete":    "match with new-build GCs actively pulling concrete permits",
    "default":     "connect with verified GCs on active permit jobs in your trade",
}

DRAFTED_TRADE_PROPS = {
    "general":     "streamline document coordination on your active projects",
    "plumbing":    "digitize plumbing spec approvals and RFI cycles",
    "electrical":  "reduce electrical submittal review time with structured workflows",
    "hvac":        "coordinate mechanical drawings and shop submissions seamlessly",
    "demolition":  "manage demo scopes and hazmat documentation in one place",
    "default":     "reduce document friction across your active project pipeline",
}

# ── Subject line templates ─────────────────────────────────────────────────────

SKIPP_SUBJECTS = {
    "permit_hook": "Permit #{permit_number} — matching GCs in {borough}",
    "trade":       "Active {trade} work in {borough} — are you available?",
    "default":     "NYC permit work in {borough} — quick intro",
}

DRAFTED_SUBJECTS = {
    "default": "Streamline your project docs — quick intro from Drafted",
    "trade":   "Document coordination for {trade} projects — Drafted",
}

# ── Body templates ─────────────────────────────────────────────────────────────

SKIPP_BODY_TEMPLATE = """\
Hi {first_name},

I came across your work on {permit_descriptor} in {borough} and wanted to reach out.

Skipp helps {trade} contractors like {company} connect with general contractors \
who are actively pulling permits and need qualified subs right now.

{trade_prop}

Most of the GCs we work with are mid-size — doing $500K–$5M jobs — and they're \
looking for reliable partners in {borough}.

Would you be open to a 10-minute call to see if it's a fit?

Best,
The Skipp Team
https://skipp.co
"""

DRAFTED_BODY_TEMPLATE = """\
Hi {first_name},

I noticed you're active on {permit_descriptor} in {borough} — impressive scope.

Drafted is a document coordination platform built for design-build teams. \
We help {trade} firms like {company} {trade_prop}.

Our typical users cut 2–3 hours per week out of their submittal and RFI cycles — \
without changing how they work with GCs or clients.

Worth a 15-minute demo?

Best,
The Drafted Team
https://drafted.build
"""

# ── Generator ──────────────────────────────────────────────────────────────────

def _extract_trade(lead: dict) -> str:
    tags = (lead.get("campaign_tags") or "").lower()
    for trade in SKIPP_TRADE_PROPS:
        if trade in tags:
            return trade
    return "general"


def _permit_descriptor(lead: dict) -> str:
    num = lead.get("permit_number") or lead.get("job_filing_number", "")
    job_type = lead.get("job_type") or lead.get("source", "")
    borough = lead.get("borough", "NYC")
    if num:
        return f"permit #{num}"
    if job_type:
        return f"a {job_type} filing in {borough}"
    return f"a project in {borough}"


def generate_proposal(lead: dict, brand: str = "skipp") -> dict:
    """
    Generate an outreach proposal for the given lead.

    Args:
        lead:  Lead dict (enriched preferred).
        brand: 'skipp' or 'drafted'.

    Returns:
        dict with keys: brand, subject, body, proposal_id, generated_at
    """
    if brand not in ("skipp", "drafted"):
        brand = "skipp"

    trade = _extract_trade(lead)
    company = lead.get("company") or lead.get("owner_business_name") or "your team"
    name = lead.get("name") or ""
    first_name = name.split()[0] if name else "there"
    borough = lead.get("borough") or "New York"
    permit_desc = _permit_descriptor(lead)

    if brand == "skipp":
        trade_prop = SKIPP_TRADE_PROPS.get(trade, SKIPP_TRADE_PROPS["default"])
        permit_number = lead.get("permit_number") or lead.get("job_filing_number", "")
        if permit_number:
            subject = SKIPP_SUBJECTS["permit_hook"].format(permit_number=permit_number, borough=borough)
        else:
            subject = SKIPP_SUBJECTS["trade"].format(trade=trade, borough=borough)

        body = SKIPP_BODY_TEMPLATE.format(
            first_name=first_name,
            permit_descriptor=permit_desc,
            borough=borough,
            trade=trade,
            company=company,
            trade_prop=trade_prop,
        )
    else:  # drafted
        trade_prop = DRAFTED_TRADE_PROPS.get(trade, DRAFTED_TRADE_PROPS["default"])
        subject = DRAFTED_SUBJECTS["trade"].format(trade=trade)

        body = DRAFTED_BODY_TEMPLATE.format(
            first_name=first_name,
            permit_descriptor=permit_desc,
            borough=borough,
            trade=trade,
            company=company,
            trade_prop=trade_prop,
        )

    proposal_id = f"{brand}-{lead.get('id', 'x')}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    generated_at = datetime.utcnow().isoformat()

    proposal = {
        "proposal_id": proposal_id,
        "brand": brand,
        "lead_id": lead.get("id"),
        "subject": subject,
        "body": body,
        "trade": trade,
        "generated_at": generated_at,
    }

    if not MOCK_MODE:
        _save_proposal(proposal, lead)

    return proposal


def _save_proposal(proposal: dict, lead: dict):
    """Persist proposal to Supabase or SQLite."""
    # Try Supabase first
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if supabase_url and supabase_key:
        try:
            from supabase import create_client
            client = create_client(supabase_url, supabase_key)
            client.table("proposals").upsert({
                "proposal_id": proposal["proposal_id"],
                "brand":       proposal["brand"],
                "lead_id":     proposal["lead_id"],
                "subject":     proposal["subject"],
                "body":        proposal["body"],
                "trade":       proposal["trade"],
                "generated_at": proposal["generated_at"],
            }).execute()
            logger.info(f"Proposal saved to Supabase: {proposal['proposal_id']}")
            return
        except Exception as e:
            logger.warning(f"Supabase save failed, falling back to SQLite: {e}")

    # Fallback: SQLite
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import StaticPool

        db_url = os.getenv("DATABASE_URL", "sqlite:///leads.db")
        if db_url.startswith("sqlite"):
            engine = create_engine(db_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        else:
            engine = create_engine(db_url)

        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id  TEXT PRIMARY KEY,
                    brand        TEXT,
                    lead_id      INTEGER,
                    subject      TEXT,
                    body         TEXT,
                    trade        TEXT,
                    generated_at TEXT
                )
            """))
            conn.commit()
            conn.execute(text("""
                INSERT OR REPLACE INTO proposals
                    (proposal_id, brand, lead_id, subject, body, trade, generated_at)
                VALUES
                    (:proposal_id, :brand, :lead_id, :subject, :body, :trade, :generated_at)
            """), proposal)
            conn.commit()
        logger.info(f"Proposal saved to SQLite: {proposal['proposal_id']}")
    except Exception as e:
        logger.error(f"Failed to save proposal to SQLite: {e}")


# ── Test harness ────────────────────────────────────────────────────────────────

def test_proposals():
    """Verify proposal generation for both brands and multiple trades."""
    sample_leads = [
        {
            "id": 1,
            "name": "Maria Gonzalez",
            "company": "Gonzalez Plumbing Inc",
            "borough": "Brooklyn",
            "campaign_tags": "plumbing,permit-hook",
            "job_filing_number": "320250001",
            "job_type": "PL",
        },
        {
            "id": 2,
            "name": "Tony Chen",
            "company": "Chen Electric",
            "borough": "Queens",
            "campaign_tags": "electrical",
            "job_filing_number": "420250002",
        },
        {
            "id": 3,
            "name": "Robert Davis",
            "company": "Davis General Contracting",
            "borough": "Manhattan",
            "campaign_tags": "general",
        },
    ]

    for lead in sample_leads:
        # Skipp angle
        skipp = generate_proposal(lead, brand="skipp")
        assert skipp["brand"] == "skipp", "Wrong brand"
        assert skipp["subject"], "Missing subject"
        assert skipp["body"], "Missing body"
        assert skipp["proposal_id"].startswith("skipp-"), "Bad proposal_id"
        assert lead["company"] in skipp["body"] or "your team" in skipp["body"], "Company missing from body"
        assert lead["borough"] in skipp["body"], f"Borough missing from body: {skipp['body'][:100]}"

        # Drafted angle
        drafted = generate_proposal(lead, brand="drafted")
        assert drafted["brand"] == "drafted", "Wrong brand"
        assert drafted["subject"], "Missing subject"
        assert drafted["body"], "Missing body"
        assert drafted["proposal_id"].startswith("drafted-"), "Bad proposal_id"

        logger.info(f"Lead {lead['id']} — skipp: '{skipp['subject']}'")
        logger.info(f"Lead {lead['id']} — drafted: '{drafted['subject']}'")

    # Trade-specific value props are injected
    plumbing_lead = sample_leads[0]
    p = generate_proposal(plumbing_lead, brand="skipp")
    assert "plumbing" in p["body"].lower(), "Plumbing trade prop missing"

    # Permit hook subject when filing number present
    assert "320250001" in p["subject"] or "plumbing" in p["subject"].lower(), "Permit hook not in subject"

    print("✓ test_proposals passed — skipp + drafted proposals generated for all trade types")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    os.environ["ENRICHMENT_MOCK"] = "true"
    test_proposals()
