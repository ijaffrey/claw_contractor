"""
NYC DOB NOW Permit Scraper

Pulls active building permits from the NYC Department of Buildings
via the Socrata Open Data API (NYC Open Data portal).

Datasets used:
- DOB Job Application Filings (ic3t-wcy2): Job applications with applicant details
  Fields: job__, job_type, borough, pre__filing_date, latest_action_date,
          applicant_s_first_name/last_name, applicant_license__, applicant_professional_title,
          owner_s_first_name/last_name, owner_s_business_name, owner_sphone__,
          initial_cost, house__, street_name, block, lot, bin__, building_type,
          other_description, job_status, job_status_descrp

- DOB NOW Build Approved Permits (rbx6-tga4): Approved permits with richer contractor info
  Fields: job_filing_number, filing_reason, permit_status, work_type, job_description,
          applicant_first_name/last_name, applicant_license, applicant_business_name,
          permittee_s_license_type, owner_name, owner_business_name,
          estimated_job_costs, house_no, street_name, borough, zip_code, block, lot, bin,
          latitude, longitude, tracking_number
"""

import os
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional

from scrapers.retry_utils import with_retry, rate_limit_delay

logger = logging.getLogger(__name__)

# NYC Open Data Socrata API endpoints (verified working)
DOB_JOB_FILINGS = "https://data.cityofnewyork.us/resource/ic3t-wcy2.json"
DOB_NOW_APPROVED = "https://data.cityofnewyork.us/resource/rbx6-tga4.json"

# Socrata pagination limit
MAX_PAGE_SIZE = 1000
DEFAULT_DAYS_BACK = 90
MAX_RECORDS = 50000  # Safety cap to prevent unbounded downloads

# Borough code mapping
BOROUGH_MAP = {
    "1": "Manhattan",
    "2": "Bronx",
    "3": "Brooklyn",
    "4": "Queens",
    "5": "Staten Island",
    "MANHATTAN": "Manhattan",
    "BRONX": "Bronx",
    "BROOKLYN": "Brooklyn",
    "QUEENS": "Queens",
    "STATEN ISLAND": "Staten Island",
}


class NYCPermitScraper:
    """Scrapes active building permits from NYC DOB NOW public data."""

    def __init__(self, app_token: Optional[str] = None):
        """
        Args:
            app_token: Optional Socrata app token for higher rate limits.
                       Works without one, but throttled to ~1 req/sec.
        """
        self.app_token = app_token or os.getenv("NYC_OPEN_DATA_APP_TOKEN")
        self.session = requests.Session()
        if self.app_token:
            self.session.headers["X-App-Token"] = self.app_token
        self.session.headers["Accept"] = "application/json"
        self._last_request_time = 0

    def _rate_limit(self):
        """Enforce minimum delay between requests."""
        min_delay = 0.5 if self.app_token else 1.0
        elapsed = time.time() - self._last_request_time
        if elapsed < min_delay:
            rate_limit_delay(min_delay - elapsed)
        self._last_request_time = time.time()

    @with_retry(max_attempts=3, backoff_seconds=[5, 15, 30])
    def _fetch_page(self, endpoint: str, params: dict) -> list:
        """Fetch a single page from the Socrata API."""
        self._rate_limit()
        resp = self.session.get(endpoint, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        logger.error(f"API returned non-list response: {str(data)[:200]}")
        return []

    def _fetch_all_pages(self, endpoint: str, base_params: dict) -> list:
        """Paginate through all results with safety cap."""
        all_records = []
        offset = 0

        while offset < MAX_RECORDS:
            params = {**base_params, "$limit": MAX_PAGE_SIZE, "$offset": offset}
            page = self._fetch_page(endpoint, params)

            if not page:
                break

            all_records.extend(page)
            logger.info(f"Fetched {len(all_records)} records so far (offset={offset})")

            if len(page) < MAX_PAGE_SIZE:
                break  # Last page

            offset += MAX_PAGE_SIZE

        logger.info(f"Total records fetched: {len(all_records)}")
        return all_records

    def scrape_job_filings(self, days_back: int = DEFAULT_DAYS_BACK,
                           borough: Optional[str] = None) -> list:
        """
        Scrape from DOB Job Application Filings (ic3t-wcy2).
        Note: This dataset has historical data (may not be current).
        Uses dobrundate for date filtering.

        Args:
            days_back: How many days back to scrape.
            borough: Filter by borough.

        Returns:
            List of normalized permit dicts.
        """
        params = {}
        where_clauses = []

        if borough:
            borough_upper = borough.upper()
            where_clauses.append(f"borough = '{borough_upper}'")

        if where_clauses:
            params["$where"] = " AND ".join(where_clauses)
        params["$order"] = "dobrundate DESC"

        logger.info(f"Scraping DOB job filings: borough={borough}")
        raw_filings = self._fetch_all_pages(DOB_JOB_FILINGS, params)
        return [self._normalize_job_filing(r) for r in raw_filings]

    def scrape_approved_permits(self, days_back: int = DEFAULT_DAYS_BACK,
                                borough: Optional[str] = None) -> list:
        """
        Scrape from DOB NOW Build Approved Permits (rbx6-tga4).
        This dataset has richer contractor/applicant and cost details.

        Args:
            days_back: How many days back to scrape.
            borough: Filter by borough.

        Returns:
            List of normalized permit dicts.
        """
        # This dataset doesn't have a reliable date column for SoQL filtering,
        # so we fetch recent records ordered by tracking_number (most recent first)
        params = {
            "$order": "tracking_number DESC",
        }
        if borough:
            borough_upper = borough.upper()
            params["$where"] = f"borough = '{borough_upper}'"

        logger.info(f"Scraping DOB NOW approved permits: borough={borough}")
        raw_permits = self._fetch_all_pages(DOB_NOW_APPROVED, params)
        return [self._normalize_approved_permit(r) for r in raw_permits]

    def _normalize_job_filing(self, raw: dict) -> dict:
        """Normalize a DOB Job Application Filings record (ic3t-wcy2)."""
        borough_raw = raw.get("borough", "")
        borough = BOROUGH_MAP.get(borough_raw.upper(), borough_raw) if borough_raw else None

        owner_first = raw.get("owner_s_first_name", "") or ""
        owner_last = raw.get("owner_s_last_name", "") or ""
        owner_biz = raw.get("owner_s_business_name", "") or ""
        owner_name = f"{owner_first} {owner_last}".strip() or owner_biz

        applicant_first = raw.get("applicant_s_first_name", "") or ""
        applicant_last = raw.get("applicant_s_last_name", "") or ""

        return {
            "job_filing_number": raw.get("job__", ""),
            "permit_type": raw.get("job_type", ""),
            "permit_subtype": "",
            "permit_status": raw.get("job_status_descrp", "") or raw.get("job_status", ""),
            "filing_date": self._parse_date(raw.get("pre__filing_date")),
            "issuance_date": self._parse_date(raw.get("fully_permitted")),
            "expiration_date": None,
            "job_description": raw.get("other_description", ""),
            "building_address": self._build_address_filing(raw),
            "borough": borough,
            "zip_code": "",
            "block": raw.get("block", ""),
            "lot": raw.get("lot", ""),
            "bin_number": raw.get("bin__", ""),
            "community_board": raw.get("community___board", ""),
            "estimated_job_cost": self._parse_cost(raw.get("initial_cost")),
            "owner_name": owner_name,
            "owner_phone": raw.get("owner_sphone__", ""),
            "owner_email": "",
            "applicant_name": f"{applicant_first} {applicant_last}".strip(),
            "applicant_license_number": raw.get("applicant_license__", ""),
            "applicant_license_type": raw.get("applicant_professional_title", ""),
            "filing_representative": "",
            "work_type": raw.get("job_type", ""),
            "building_type": raw.get("building_type", ""),
            "raw_data": raw,
        }

    def _normalize_approved_permit(self, raw: dict) -> dict:
        """Normalize a DOB NOW Build Approved Permits record (rbx6-tga4)."""
        borough_raw = raw.get("borough", "")
        borough = BOROUGH_MAP.get(borough_raw.upper(), borough_raw) if borough_raw else None

        applicant_first = raw.get("applicant_first_name", "") or ""
        applicant_last = raw.get("applicant_last_name", "") or ""
        applicant_biz = raw.get("applicant_business_name", "") or ""

        return {
            "job_filing_number": raw.get("tracking_number", "") or raw.get("job_filing_number", ""),
            "permit_type": raw.get("filing_reason", ""),
            "permit_subtype": raw.get("work_type", ""),
            "permit_status": raw.get("permit_status", ""),
            "filing_date": None,  # Not reliably available
            "issuance_date": None,
            "expiration_date": None,
            "job_description": raw.get("job_description", ""),
            "building_address": self._build_address_approved(raw),
            "borough": borough,
            "zip_code": raw.get("zip_code", ""),
            "block": raw.get("block", ""),
            "lot": raw.get("lot", ""),
            "bin_number": raw.get("bin", ""),
            "community_board": raw.get("community_board", "") or raw.get("c_b_no", ""),
            "estimated_job_cost": self._parse_cost(raw.get("estimated_job_costs")),
            "owner_name": raw.get("owner_name", ""),
            "owner_phone": "",
            "owner_email": "",
            "applicant_name": f"{applicant_first} {applicant_last}".strip() or applicant_biz,
            "applicant_license_number": raw.get("applicant_license", ""),
            "applicant_license_type": raw.get("permittee_s_license_type", ""),
            "filing_representative": (
                (raw.get("filing_representative_first_name", "") or "") + " " +
                (raw.get("filing_representative_last_name", "") or "")
            ).strip(),
            "work_type": raw.get("work_type", ""),
            "building_type": "",
            "raw_data": raw,
        }

    def _build_address_filing(self, raw: dict) -> str:
        """Build address from DOB Job Filing fields."""
        house = raw.get("house__", "") or ""
        street = raw.get("street_name", "") or ""
        addr = f"{house} {street}".strip()
        borough = raw.get("borough", "")
        if addr and borough:
            addr = f"{addr}, {borough}, NY"
        return addr

    def _build_address_approved(self, raw: dict) -> str:
        """Build address from DOB NOW Approved Permit fields."""
        house = raw.get("house_no", "") or ""
        street = raw.get("street_name", "") or ""
        addr = f"{house} {street}".strip()
        borough = raw.get("borough", "") or ""
        zipcode = raw.get("zip_code", "") or ""
        if addr:
            parts = [addr]
            if borough:
                parts.append(borough)
            parts.append("NY")
            if zipcode:
                parts.append(zipcode)
            addr = ", ".join(parts)
        return addr

    def _parse_date(self, val) -> Optional[str]:
        """Parse various date formats from Socrata."""
        if not val:
            return None
        if isinstance(val, str):
            # Try multiple formats the API may return
            for fmt in (
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
                "%m/%d/%Y %H:%M:%S",
                "%m/%d/%Y",
            ):
                try:
                    return datetime.strptime(val.strip()[:26], fmt).isoformat()
                except ValueError:
                    continue
        return str(val) if val else None

    def _parse_cost(self, val) -> Optional[float]:
        """Parse cost/dollar values."""
        if not val:
            return None
        try:
            cleaned = str(val).replace("$", "").replace(",", "").strip()
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None
