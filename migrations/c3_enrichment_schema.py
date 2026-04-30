"""
C3 Enrichment Schema Migration

Adds enrichment columns to leads table.
Creates campaigns table and campaign_leads junction table.
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Use SQLite for local dev; Supabase for prod
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///leads.db")


def _get_engine():
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    if DATABASE_URL.startswith("sqlite"):
        return create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(DATABASE_URL)


def run_migration(engine=None):
    """Add C3 enrichment columns and tables."""
    from sqlalchemy import text

    if engine is None:
        engine = _get_engine()

    with engine.connect() as conn:
        # --- Enrichment columns on leads ---
        enrichment_columns = [
            # Contact info (may differ from original email/phone already on the model)
            ("enriched_email", "TEXT"),
            ("enriched_phone", "TEXT"),
            ("website", "TEXT"),
            ("email_source", "TEXT"),
            ("phone_source", "TEXT"),
            # Enrichment metadata
            ("enrichment_status", "TEXT DEFAULT 'pending'"),
            ("enrichment_score", "REAL DEFAULT 0.0"),
            ("enriched_at", "TEXT"),
            # Campaign / outreach
            ("campaign_tags", "TEXT"),  # JSON array stored as string
            ("outreach_status", "TEXT DEFAULT 'none'"),
            ("last_contacted_at", "TEXT"),
            # General notes (column already exists in the model as TEXT nullable,
            # so we skip it to avoid duplicate-column errors)
        ]

        for col_name, col_def in enrichment_columns:
            try:
                conn.execute(text(f"ALTER TABLE leads ADD COLUMN {col_name} {col_def}"))
                conn.commit()
                logger.info(f"Added column leads.{col_name}")
            except Exception as e:
                # Column already exists — safe to continue
                if (
                    "duplicate column" in str(e).lower()
                    or "already exists" in str(e).lower()
                ):
                    logger.debug(f"Column leads.{col_name} already exists, skipping")
                else:
                    logger.warning(f"Could not add leads.{col_name}: {e}")

        # --- Campaigns table ---
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                description TEXT,
                brand       TEXT NOT NULL DEFAULT 'skipp',
                status      TEXT NOT NULL DEFAULT 'draft',
                target_trade TEXT,
                target_borough TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
                launched_at TEXT,
                stats       TEXT DEFAULT '{}'
            )
        """))
        conn.commit()
        logger.info("Ensured campaigns table exists")

        # --- Campaign-leads junction table ---
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS campaign_leads (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id     INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                lead_id         INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                added_at        TEXT NOT NULL DEFAULT (datetime('now')),
                outreach_status TEXT NOT NULL DEFAULT 'pending',
                sent_at         TEXT,
                opened_at       TEXT,
                replied_at      TEXT,
                proposal_id     TEXT,
                UNIQUE(campaign_id, lead_id)
            )
        """))
        conn.commit()
        logger.info("Ensured campaign_leads table exists")

    return True


def test_schema():
    """Verify migration runs and all expected columns/tables exist."""
    from sqlalchemy import text, inspect

    engine = _get_engine()

    # Run the migration (idempotent)
    run_migration(engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    # Check campaigns table
    assert "campaigns" in tables, "campaigns table missing"
    assert "campaign_leads" in tables, "campaign_leads table missing"
    assert "leads" in tables, "leads table missing"

    # Check enrichment columns on leads
    lead_cols = {c["name"] for c in inspector.get_columns("leads")}
    required = {
        "enriched_email",
        "enriched_phone",
        "website",
        "email_source",
        "phone_source",
        "enrichment_status",
        "enrichment_score",
        "enriched_at",
        "campaign_tags",
        "outreach_status",
        "last_contacted_at",
    }
    missing = required - lead_cols
    assert not missing, f"Missing lead columns: {missing}"

    # Check campaigns columns
    camp_cols = {c["name"] for c in inspector.get_columns("campaigns")}
    for col in ("id", "name", "brand", "status", "created_at"):
        assert col in camp_cols, f"campaigns.{col} missing"

    # Check junction table columns
    junc_cols = {c["name"] for c in inspector.get_columns("campaign_leads")}
    for col in ("campaign_id", "lead_id", "outreach_status"):
        assert col in junc_cols, f"campaign_leads.{col} missing"

    print("✓ test_schema passed — all tables and columns present")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()
    print("Migration complete.")
