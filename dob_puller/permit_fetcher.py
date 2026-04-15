"""Query DOB NOW Socrata endpoints for permit metadata by BIN/address."""

import logging
from typing import Optional

from . import http_utils

log = logging.getLogger(__name__)

# DOB NOW: Build – Job Application Filings
JOB_FILINGS_ENDPOINT = "https://data.cityofnewyork.us/resource/ipu4-2q9a.json"
# DOB NOW: Build – Approved Permits
APPROVED_PERMITS_ENDPOINT = "https://data.cityofnewyork.us/resource/rbx6-tga4.json"
# DOB NOW: Build – Approved Permit Applications (has job_type + initial_cost
# + total_construction_floor_area — the only active dataset that carries
# the scope area per filing).
BUILD_APPROVED_APPS_ENDPOINT = (
    "https://data.cityofnewyork.us/resource/w9ak-ipjd.json"
)

MAX_ROWS_PER_DATASET = 500  # hard cap to prevent unbounded download


def _fetch_paginated(
    endpoint: str,
    where: str,
    *,
    limit: int = MAX_ROWS_PER_DATASET,
    page_size: int = 100,
) -> list:
    """Fetch rows from a Socrata endpoint with pagination and a hard cap."""
    out: list = []
    offset = 0
    while len(out) < limit:
        batch = min(page_size, limit - len(out))
        params = {"$where": where, "$limit": batch, "$offset": offset}
        try:
            resp = http_utils.get(endpoint, params=params)
            rows = resp.json()
        except Exception as exc:
            log.error("Fetch failed %s: %s", endpoint, exc)
            break
        if not rows:
            break
        out.extend(rows)
        log.info(
            "Fetched %d rows from %s (total %d)", len(rows), endpoint, len(out)
        )
        if len(rows) < batch:
            break
        offset += batch
    if len(out) >= limit:
        log.warning(
            "Hit row cap %d for %s — results may be truncated", limit, endpoint
        )
    return out


def fetch_job_filings(
    bin_: Optional[str] = None,
    house_number: Optional[str] = None,
    street: Optional[str] = None,
    borough: Optional[str] = None,
) -> list:
    """Fetch DOB NOW job filings filtered by BIN or address."""
    clauses = []
    if bin_:
        clauses.append(f"bin__='{bin_}'")
    else:
        if house_number:
            clauses.append(f"house__='{house_number}'")
        if street:
            clauses.append(f"upper(street_name)=upper('{street}')")
        if borough:
            clauses.append(f"upper(borough)=upper('{borough}')")
    if not clauses:
        raise ValueError("fetch_job_filings needs bin_ or address components")
    where = " AND ".join(clauses)
    log.info("Job filings query: %s", where)
    return _fetch_paginated(JOB_FILINGS_ENDPOINT, where)


def fetch_build_approved_apps(
    bin_: Optional[str] = None,
    house_number: Optional[str] = None,
    street: Optional[str] = None,
    borough: Optional[str] = None,
) -> list:
    """Fetch DOB NOW Build Approved Permit Applications (w9ak-ipjd).

    This dataset carries total_construction_floor_area and initial_cost
    per filing — fields that rbx6-tga4 lacks.
    """
    clauses = []
    if bin_:
        clauses.append(f"bin='{bin_}'")
    else:
        if house_number:
            clauses.append(f"house_no='{house_number}'")
        if street:
            clauses.append(f"upper(street_name)=upper('{street}')")
        if borough:
            clauses.append(f"upper(borough)=upper('{borough}')")
    if not clauses:
        raise ValueError(
            "fetch_build_approved_apps needs bin_ or address components"
        )
    where = " AND ".join(clauses)
    log.info("Build Approved Apps query: %s", where)
    return _fetch_paginated(BUILD_APPROVED_APPS_ENDPOINT, where)


def fetch_approved_permits(
    bin_: Optional[str] = None,
    house_number: Optional[str] = None,
    street: Optional[str] = None,
    borough: Optional[str] = None,
) -> list:
    """Fetch DOB NOW approved permits filtered by BIN or address."""
    clauses = []
    if bin_:
        clauses.append(f"bin='{bin_}'")
    else:
        if house_number:
            clauses.append(f"house_no='{house_number}'")
        if street:
            clauses.append(f"upper(street_name)=upper('{street}')")
        if borough:
            clauses.append(f"upper(borough)=upper('{borough}')")
    if not clauses:
        raise ValueError("fetch_approved_permits needs bin_ or address components")
    where = " AND ".join(clauses)
    log.info("Approved permits query: %s", where)
    return _fetch_paginated(APPROVED_PERMITS_ENDPOINT, where)


def fetch_all_permits(resolved: dict) -> dict:
    """Given an address_resolver result, fetch from all DOB NOW datasets."""
    bin_ = resolved.get("bin")
    job_filings = []
    approved_permits = []
    build_approved_apps = []

    # Try BIN first (most precise), fall back to address components
    try:
        if bin_:
            job_filings = fetch_job_filings(bin_=bin_)
        if not job_filings:
            job_filings = fetch_job_filings(
                house_number=resolved.get("house_number"),
                street=resolved.get("street"),
            )
    except Exception as exc:
        log.error("Job filings fetch error: %s", exc)

    try:
        if bin_:
            approved_permits = fetch_approved_permits(bin_=bin_)
        if not approved_permits:
            approved_permits = fetch_approved_permits(
                house_number=resolved.get("house_number"),
                street=resolved.get("street"),
            )
    except Exception as exc:
        log.error("Approved permits fetch error: %s", exc)

    try:
        if bin_:
            build_approved_apps = fetch_build_approved_apps(bin_=bin_)
        if not build_approved_apps:
            build_approved_apps = fetch_build_approved_apps(
                house_number=resolved.get("house_number"),
                street=resolved.get("street"),
            )
    except Exception as exc:
        log.error("Build approved apps fetch error: %s", exc)

    return {
        "job_filings": job_filings,
        "approved_permits": approved_permits,
        "build_approved_apps": build_approved_apps,
    }
