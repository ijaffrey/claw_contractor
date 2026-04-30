"""
NYC Permit Scraper — Main Orchestrator

Usage:
    python3 run_permit_scraper.py [--days 90] [--borough Manhattan] [--dry-run]

Pipeline:
    1. Scrape permits from NYC DOB NOW public data
    2. Extract and upsert contractor profiles
    3. Match general contractors with relevant subcontractors
    4. Store everything in Supabase
"""

import argparse
import logging
import sys
from datetime import datetime

from nyc_permit_scraper import NYCPermitScraper
from permit_store import (
    upsert_permits_batch,
    upsert_contractor_profile,
    get_contractor_profiles,
    insert_match,
    get_recent_filing_numbers,
)
from permit_matcher import find_matches, get_relevant_trades

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("permit_scraper.log"),
    ],
)
logger = logging.getLogger("permit_pipeline")


def extract_contractor_profile(permit: dict) -> dict | None:
    """Extract a contractor profile from a permit record."""
    license_num = permit.get("applicant_license_number", "").strip()
    name = permit.get("applicant_name", "").strip()

    if not license_num and not name:
        return None

    borough = permit.get("borough")
    permit_type = permit.get("permit_type", "")
    trades = get_relevant_trades(permit_type)
    cost = permit.get("estimated_job_cost")

    # Determine role based on license type
    # DOB NOW codes: GC=General Contractor, P=Plumber, F=Fire Suppression,
    # RA=Registered Architect, PE=Professional Engineer, E=Electrician
    license_type = (permit.get("applicant_license_type") or "").upper().strip()
    sub_types = {
        "P",
        "PLUMBER",
        "MASTER PLUMBER",
        "F",
        "FIRE SUPPRESSION",
        "E",
        "ELECTRICIAN",
        "MASTER ELECTRICIAN",
    }
    gc_types = {"GC", "GENERAL CONTRACTOR", "PE", "RA", "ARCHITECT", "ENGINEER"}

    if license_type in sub_types or any(t in license_type for t in sub_types):
        role = "sub"
    elif license_type in gc_types or any(t in license_type for t in gc_types):
        role = "general"
    else:
        role = "general"

    return {
        "license_number": license_num or f"unlicensed_{name[:20]}",
        "company_name": name,
        "contact_name": permit.get("owner_name", "").strip() or name,
        "phone": permit.get("owner_phone", ""),
        "email": permit.get("owner_email", ""),
        "license_type": license_type,
        "contractor_role": role,
        "trade_types": trades,
        "boroughs_active": [borough] if borough else [],
        "total_permits": 1,
        "avg_project_cost": cost,
        "last_permit_date": permit.get("filing_date") or permit.get("issuance_date"),
    }


def run_pipeline(
    days_back: int = 90, borough: str | None = None, dry_run: bool = False
):
    """
    Full pipeline: scrape → extract profiles → match → store.

    Args:
        days_back: How far back to scrape.
        borough: Optional borough filter.
        dry_run: If True, scrape and log but don't write to Supabase.
    """
    logger.info("=" * 60)
    logger.info(f"NYC Permit Scraper Pipeline — {datetime.now().isoformat()}")
    logger.info(f"Config: days_back={days_back}, borough={borough}, dry_run={dry_run}")
    logger.info("=" * 60)

    scraper = NYCPermitScraper()

    # --- Step 1: Scrape permits ---
    logger.info("Step 1: Scraping permits from NYC DOB NOW...")

    # Primary source: DOB NOW Approved Permits (rbx6-tga4) — current data with rich contractor info
    approved_permits = scraper.scrape_approved_permits(
        days_back=days_back, borough=borough
    )
    logger.info(f"Scraped {len(approved_permits)} approved permits")

    # Secondary source is opt-in (DOB Job Filings has older data and is slow)
    permits = []

    # Merge and deduplicate by filing number
    seen_filings = set()
    all_permits = []
    for p in approved_permits + permits:
        fn = p.get("job_filing_number", "")
        if fn and fn not in seen_filings:
            seen_filings.add(fn)
            all_permits.append(p)

    logger.info(f"Total unique permits after dedup: {len(all_permits)}")

    if dry_run:
        logger.info("[DRY RUN] Would store %d permits. Sample:", len(all_permits))
        for p in all_permits[:3]:
            logger.info(
                f"  {p['job_filing_number']} | {p['permit_type']} | {p['borough']} | {p['building_address']}"
            )
        return {"permits": len(all_permits), "profiles": 0, "matches": 0}

    # --- Step 2: Store permits in Supabase ---
    logger.info("Step 2: Storing permits in Supabase...")
    existing = get_recent_filing_numbers()
    new_permits = [p for p in all_permits if p.get("job_filing_number") not in existing]
    logger.info(
        f"New permits to insert: {len(new_permits)} (skipping {len(all_permits) - len(new_permits)} existing)"
    )

    if new_permits:
        stats = upsert_permits_batch(new_permits)
        logger.info(f"Permit upsert: {stats}")

    # --- Step 3: Extract and store contractor profiles ---
    logger.info("Step 3: Extracting contractor profiles...")
    profiles_created = 0
    profile_map = {}  # license_number -> profile

    for permit in all_permits:
        profile = extract_contractor_profile(permit)
        if profile:
            key = (profile["license_number"], profile["contractor_role"])
            if key in profile_map:
                # Update existing: merge boroughs, increment count, update cost avg
                existing_profile = profile_map[key]
                existing_boroughs = set(existing_profile.get("boroughs_active", []))
                new_boroughs = set(profile.get("boroughs_active", []))
                existing_profile["boroughs_active"] = list(
                    existing_boroughs | new_boroughs
                )
                existing_profile["total_permits"] = (
                    existing_profile.get("total_permits", 0) + 1
                )
                # Running average of cost
                old_cost = existing_profile.get("avg_project_cost") or 0
                new_cost = profile.get("avg_project_cost") or 0
                if old_cost and new_cost:
                    count = existing_profile["total_permits"]
                    existing_profile["avg_project_cost"] = (
                        old_cost * (count - 1) + new_cost
                    ) / count
                elif new_cost:
                    existing_profile["avg_project_cost"] = new_cost
                # Merge trade types
                existing_trades = set(existing_profile.get("trade_types", []))
                new_trades = set(profile.get("trade_types", []))
                existing_profile["trade_types"] = list(existing_trades | new_trades)
            else:
                profile_map[key] = profile

    logger.info(f"Unique contractor profiles extracted: {len(profile_map)}")

    for profile in profile_map.values():
        result = upsert_contractor_profile(profile)
        if result:
            profiles_created += 1

    logger.info(f"Contractor profiles stored: {profiles_created}")

    # --- Step 4: Match GCs with subcontractors ---
    logger.info("Step 4: Matching general contractors with subcontractors...")
    gc_profiles = get_contractor_profiles(role="general")
    sub_profiles = get_contractor_profiles(role="sub")
    logger.info(
        f"Found {len(gc_profiles)} GCs and {len(sub_profiles)} subs in database"
    )

    # Get stored permits (with IDs) for matching
    from permit_store import get_permits

    stored_permits = get_permits(borough=borough, limit=500)

    matches_created = 0
    for permit in stored_permits:
        # Find the GC associated with this permit
        permit_license = permit.get("applicant_license_number", "")
        gc = next(
            (g for g in gc_profiles if g.get("license_number") == permit_license), None
        )
        if not gc:
            continue

        matches = find_matches(permit, gc, sub_profiles, min_score=30)
        for match in matches[:5]:  # Top 5 matches per permit
            result = insert_match(match)
            if result:
                matches_created += 1

    logger.info(f"Matches created: {matches_created}")

    # --- Summary ---
    summary = {
        "permits_scraped": len(all_permits),
        "permits_new": len(new_permits),
        "profiles_stored": profiles_created,
        "matches_created": matches_created,
        "timestamp": datetime.now().isoformat(),
    }
    logger.info("=" * 60)
    logger.info(f"Pipeline complete: {summary}")
    logger.info("=" * 60)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NYC Permit Scraper Pipeline")
    parser.add_argument(
        "--days", type=int, default=90, help="Days back to scrape (default: 90)"
    )
    parser.add_argument(
        "--borough",
        type=str,
        default=None,
        help="Filter by borough (Manhattan, Bronx, Brooklyn, Queens, Staten Island)",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=50000,
        help="Max records to fetch per dataset (default: 50000)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and log without writing to Supabase",
    )
    args = parser.parse_args()

    # Set max records on scraper module
    import nyc_permit_scraper

    nyc_permit_scraper.MAX_RECORDS = args.max_records

    run_pipeline(days_back=args.days, borough=args.borough, dry_run=args.dry_run)
