"""
Lead Store — Supabase CRUD for the leads table.

Follows the permit_store.py pattern: lazy-init client, upsert on
(customer_email, email_thread_id) for deduplication on re-runs.
"""

import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_supabase_client = None


def _get_client():
    """Get or create the Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY environment variables are required."
            )
        _supabase_client = create_client(url, key)
    return _supabase_client


def upsert_lead(lead: dict) -> Optional[dict]:
    """
    Insert or update a lead record in Supabase.

    Stores all standard fields plus the four enrichment fields:
        job_type_classification, value_tier, urgency_score, one_line_summary.

    Deduplicates on email_thread_id when present; falls back to insert.

    Args:
        lead: Flat lead dict as returned by lead_parser.parse_lead().

    Returns:
        The upserted record dict, or None on failure.
    """
    client = _get_client()

    record = {
        "customer_name":          lead.get("customer_name"),
        "customer_email":         lead.get("customer_email"),
        "phone":                  lead.get("phone"),
        "job_type":               lead.get("job_type"),
        "description":            lead.get("description"),
        "location":               lead.get("location"),
        "source":                 lead.get("source"),
        "urgency":                lead.get("urgency"),
        "raw_subject":            lead.get("raw_subject"),
        "raw_body":               lead.get("raw_body"),
        # Enrichment fields
        "job_type_classification": lead.get("job_type_classification"),
        "value_tier":             lead.get("value_tier"),
        "urgency_score":          lead.get("urgency_score"),
        "one_line_summary":       lead.get("one_line_summary"),
        "created_at":             datetime.utcnow().isoformat(),
    }

    # Include email_thread_id for deduplication if available
    thread_id = lead.get("email_thread_id")
    if thread_id:
        record["email_thread_id"] = thread_id

    try:
        if thread_id:
            result = (
                client.table("leads")
                .upsert(record, on_conflict="email_thread_id")
                .execute()
            )
        else:
            result = client.table("leads").insert(record).execute()

        if result.data:
            stored = result.data[0]
            logger.info(f"Lead stored: id={stored.get('id')} email={record.get('customer_email')}")
            return stored
        return None
    except Exception as e:
        logger.error(f"Failed to upsert lead for {record.get('customer_email')}: {e}")
        return None
