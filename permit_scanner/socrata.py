"""NYC Open Data (Socrata) queries for permit scanning.

Primary dataset: w9ak-ipjd — DOB NOW: Build – Approved Permit Applications.
This dataset is active, covers post-2016 DOB NOW filings, and carries
the fields we need for scoring: job_type, initial_cost,
total_construction_floor_area, bin/bbl, filing_date, owner name.
"""

import datetime
import logging
from typing import Optional

import requests

log = logging.getLogger(__name__)

DOB_NOW_BUILD_ENDPOINT = (
    "https://data.cityofnewyork.us/resource/w9ak-ipjd.json"
)
PLUTO_ENDPOINT = "https://data.cityofnewyork.us/resource/64uk-42ks.json"

# w9ak-ipjd uses descriptive strings. Map Sprint-D A1/A2/DM intent to these:
#   A1/A2 (alterations) → "Alteration", "Alteration CO"
#   DM (demolition)      → "Demolition"
JOB_TYPE_FILTER = ("Alteration", "Alteration CO", "Demolition")

# Codified map for scoring rules that care about DM vs A1 separately.
JOB_TYPE_CODE = {
    "Alteration": "A1_A2",
    "Alteration CO": "A3",
    "Demolition": "DM",
    "New Building": "NB",
    "No Work": "NW",
}


PAGE_SIZE = 1000


def fetch_recent_permits(
    borough: str = "MANHATTAN",
    *,
    days_back: int = 90,
    limit: int | None = None,
    timeout: int = 60,
    job_types: tuple | None = None,
) -> list:
    """Return permits filed in the last N days for the given borough.

    Pagination: fetches in batches of PAGE_SIZE (1000) using $offset until a
    batch comes back with fewer than PAGE_SIZE rows, signaling exhaustion.
    Pass limit=N to cap early; limit=None means "pull all".

    job_types defaults to the scoring-scanner's (Alteration, Alteration CO,
    Demolition). Pass None or () to fetch ALL job types (needed by
    bucket_analyzer which wants New Building and Full Demolition too).
    """
    since = (
        datetime.date.today() - datetime.timedelta(days=days_back)
    ).isoformat()
    effective_types = JOB_TYPE_FILTER if job_types is None else tuple(job_types)
    clauses = [
        f"upper(borough)=upper('{borough}')",
        f"filing_date >= '{since}'",
    ]
    if effective_types:
        types_sql = ",".join(f"'{t}'" for t in effective_types)
        clauses.append(f"job_type in({types_sql})")
    where = " AND ".join(clauses)
    log.info(
        "Socrata query: borough=%s since=%s types=%s limit=%s page=%d",
        borough,
        since,
        effective_types or "ALL",
        "ALL" if limit is None else str(limit),
        PAGE_SIZE,
    )
    rows: list = []
    offset = 0
    while True:
        if limit is not None and len(rows) >= limit:
            break
        batch_size = PAGE_SIZE
        if limit is not None:
            batch_size = min(PAGE_SIZE, limit - len(rows))
        params = {
            "$where": where,
            "$order": "filing_date DESC",
            "$limit": batch_size,
            "$offset": offset,
        }
        try:
            resp = requests.get(
                DOB_NOW_BUILD_ENDPOINT, params=params, timeout=timeout
            )
            resp.raise_for_status()
            batch_rows = resp.json()
        except Exception as exc:
            log.error("Socrata fetch failed at offset %d: %s", offset, exc)
            break
        if not batch_rows:
            break
        rows.extend(batch_rows)
        log.info(
            "Fetched %d rows at offset=%d (cumulative %d)",
            len(batch_rows),
            offset,
            len(rows),
        )
        # Exhausted if Socrata returns fewer than a full page
        if len(batch_rows) < batch_size:
            break
        offset += batch_size
    log.info("Total permits returned: %d", len(rows))
    return rows


def batch_lookup_pluto_year(
    bbls: list, *, chunk_size: int = 100, timeout: int = 60
) -> dict:
    """Batch-query PLUTO for yearbuilt keyed by bbl.

    Returns {bbl_str: yearbuilt_int}. Unknown BBLs are simply absent.
    BBLs come from w9ak-ipjd in integer-ish form; PLUTO stores them as
    decimals like "1012840033.00000000", so we coerce both sides.
    """
    if not bbls:
        return {}
    out: dict = {}
    clean_bbls: list = []
    for b in bbls:
        if b is None:
            continue
        s = str(b).split(".")[0].strip()
        if s:
            clean_bbls.append(s)
    clean_bbls = sorted(set(clean_bbls))

    for i in range(0, len(clean_bbls), chunk_size):
        chunk = clean_bbls[i : i + chunk_size]
        where = "bbl in(" + ",".join(f"'{b}'" for b in chunk) + ")"
        params = {
            "$where": where,
            "$select": "bbl,yearbuilt,bldgarea,numfloors",
            "$limit": chunk_size,
        }
        try:
            resp = requests.get(
                PLUTO_ENDPOINT, params=params, timeout=timeout
            )
            resp.raise_for_status()
            rows = resp.json()
        except Exception as exc:
            log.warning("PLUTO batch lookup failed: %s", exc)
            continue
        for r in rows:
            raw_bbl = str(r.get("bbl", "")).split(".")[0]
            year_raw = r.get("yearbuilt")
            try:
                year = int(float(year_raw)) if year_raw not in (None, "") else None
            except (TypeError, ValueError):
                year = None
            if year and raw_bbl:
                out[raw_bbl] = {
                    "year_built": year,
                    "bldg_area_sqft": float(r["bldgarea"]) if r.get("bldgarea") not in (None, "") else None,
                    "num_floors": float(r["numfloors"]) if r.get("numfloors") not in (None, "") else None,
                }
    log.info("PLUTO lookup: %d/%d BBLs enriched", len(out), len(clean_bbls))
    return out
