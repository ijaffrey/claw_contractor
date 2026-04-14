"""
C4 Filer Enrichment Schema Migration

Adds four enrichment columns to the leads table:
    job_type_classification — structured trade/category label
    value_tier              — small | medium | large
    urgency_score           — integer 1–5
    one_line_summary        — one-sentence description of the job
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

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
    """Add C4 enrichment columns to the leads table."""
    from sqlalchemy import text

    if engine is None:
        engine = _get_engine()

    enrichment_columns = [
        ("job_type_classification", "TEXT"),
        ("value_tier",              "TEXT"),
        ("urgency_score",           "INTEGER"),
        ("one_line_summary",        "TEXT"),
    ]

    with engine.connect() as conn:
        for col_name, col_def in enrichment_columns:
            try:
                conn.execute(text(f"ALTER TABLE leads ADD COLUMN {col_name} {col_def}"))
                conn.commit()
                logger.info(f"Added column leads.{col_name}")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    logger.debug(f"Column leads.{col_name} already exists, skipping")
                else:
                    logger.warning(f"Could not add leads.{col_name}: {e}")

    return True


def test_schema():
    """Verify all four enrichment columns are present on leads."""
    from sqlalchemy import inspect

    engine = _get_engine()
    run_migration(engine)

    inspector = inspect(engine)
    lead_cols = {c["name"] for c in inspector.get_columns("leads")}
    required = {"job_type_classification", "value_tier", "urgency_score", "one_line_summary"}
    missing = required - lead_cols
    assert not missing, f"Missing lead columns: {missing}"

    print("✓ test_schema passed — all C4 enrichment columns present")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()
    print("C4 migration complete.")
