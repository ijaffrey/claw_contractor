"""
Permit Store — Supabase CRUD for permits, contractor profiles, and matches.

Uses the supabase-py client for direct Supabase access.
Handles upserts for deduplication on re-runs.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-init Supabase client
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
                "SUPABASE_URL and SUPABASE_KEY environment variables are required. "
                "Set them in your .env file or environment."
            )
        _supabase_client = create_client(url, key)
    return _supabase_client


def upsert_permit(permit: dict) -> Optional[dict]:
    """
    Insert or update a permit record. Deduplicates on job_filing_number.

    Args:
        permit: Normalized permit dict from the scraper.

    Returns:
        The upserted record dict, or None on failure.
    """
    client = _get_client()
    filing_number = permit.get("job_filing_number")
    if not filing_number:
        logger.warning("Skipping permit with no job_filing_number")
        return None

    # Serialize raw_data to JSON string if it's a dict
    record = {**permit}
    if isinstance(record.get("raw_data"), dict):
        record["raw_data"] = json.dumps(record["raw_data"])
    record["scraped_at"] = datetime.utcnow().isoformat()

    try:
        result = (
            client.table("permits")
            .upsert(record, on_conflict="job_filing_number")
            .execute()
        )
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Failed to upsert permit {filing_number}: {e}")
        return None


def upsert_permits_batch(permits: list) -> dict:
    """
    Batch upsert permits. Returns counts of inserted/updated/failed.
    """
    client = _get_client()
    stats = {"success": 0, "failed": 0, "total": len(permits)}

    # Process in chunks to avoid payload limits
    chunk_size = 100
    for i in range(0, len(permits), chunk_size):
        chunk = permits[i:i + chunk_size]
        records = []
        for p in chunk:
            if not p.get("job_filing_number"):
                stats["failed"] += 1
                continue
            record = {**p}
            if isinstance(record.get("raw_data"), dict):
                record["raw_data"] = json.dumps(record["raw_data"])
            record["scraped_at"] = datetime.utcnow().isoformat()
            records.append(record)

        if not records:
            continue

        try:
            result = (
                client.table("permits")
                .upsert(records, on_conflict="job_filing_number")
                .execute()
            )
            stats["success"] += len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"Batch upsert failed for chunk at offset {i}: {e}")
            stats["failed"] += len(records)

    return stats


def upsert_contractor_profile(profile: dict) -> Optional[dict]:
    """
    Insert or update a contractor profile.
    Deduplicates on (license_number, contractor_role).
    """
    client = _get_client()
    license_num = profile.get("license_number")
    role = profile.get("contractor_role", "general")

    if not license_num:
        logger.warning("Skipping contractor with no license_number")
        return None

    record = {**profile, "contractor_role": role}

    try:
        result = (
            client.table("contractor_profiles")
            .upsert(record, on_conflict="license_number,contractor_role")
            .execute()
        )
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Failed to upsert contractor {license_num}: {e}")
        return None


def get_contractor_profiles(role: Optional[str] = None,
                            borough: Optional[str] = None) -> list:
    """
    Fetch contractor profiles with optional filters.

    Args:
        role: Filter by contractor_role ("general" or "sub").
        borough: Filter by active borough.

    Returns:
        List of contractor profile dicts.
    """
    client = _get_client()
    query = client.table("contractor_profiles").select("*")

    if role:
        query = query.eq("contractor_role", role)
    if borough:
        query = query.contains("boroughs_active", [borough])

    try:
        result = query.execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch contractor profiles: {e}")
        return []


def insert_match(match: dict) -> Optional[dict]:
    """
    Insert a permit match record.
    Deduplicates on (permit_id, gc_profile_id, sub_profile_id).
    """
    client = _get_client()

    record = {
        "permit_id": match["permit_id"],
        "gc_profile_id": match["gc_profile_id"],
        "sub_profile_id": match["sub_profile_id"],
        "match_score": match["match_score"],
        "match_reasons": json.dumps(match.get("match_reasons", [])),
        "permit_type_match": match.get("permit_type_match", False),
        "scope_match": match.get("scope_match", False),
        "location_match": match.get("location_match", False),
        "status": "pending",
    }

    try:
        result = (
            client.table("permit_matches")
            .upsert(record, on_conflict="permit_id,gc_profile_id,sub_profile_id")
            .execute()
        )
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Failed to insert match: {e}")
        return None


def get_permits(borough: Optional[str] = None,
                permit_type: Optional[str] = None,
                limit: int = 100) -> list:
    """Fetch permits from Supabase with optional filters."""
    client = _get_client()
    query = client.table("permits").select("*").order("filing_date", desc=True).limit(limit)

    if borough:
        query = query.eq("borough", borough)
    if permit_type:
        query = query.eq("permit_type", permit_type)

    try:
        result = query.execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch permits: {e}")
        return []


def get_recent_filing_numbers(limit: int = 5000) -> set:
    """Get the set of job_filing_numbers already in the database for fast dedup checks."""
    client = _get_client()
    try:
        result = (
            client.table("permits")
            .select("job_filing_number")
            .order("scraped_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {r["job_filing_number"] for r in (result.data or [])}
    except Exception as e:
        logger.error(f"Failed to fetch existing filing numbers: {e}")
        return set()
