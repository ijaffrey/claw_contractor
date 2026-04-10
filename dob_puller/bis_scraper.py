"""Scrape https://a810-bisweb.nyc.gov/bisweb/ for pre-2016 permits + documents.

BIS (Buildings Information System) is the legacy DOB system. Given a BIN,
we can open the Property Profile page and walk the Jobs list to collect
job numbers and any document/scan links.
"""

import logging
import re
import time
from typing import Optional
from urllib.parse import urljoin

import requests

from . import http_utils

log = logging.getLogger(__name__)

BIS_BASE = "https://a810-bisweb.nyc.gov/bisweb/"
PROPERTY_PROFILE = (
    "https://a810-bisweb.nyc.gov/bisweb/PropertyProfileOverviewServlet"
)
JOBS_FOR_BIN = "https://a810-bisweb.nyc.gov/bisweb/JobsQueryByLocationServlet"

REQUEST_DELAY = 1.0  # polite delay between BIS requests
MAX_JOBS_TO_DETAIL = 25  # hard cap — avoid multi-minute scrapes
BIS_TIMEOUT = 20  # per-request timeout for BIS pages

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_jobs_for_bin(bin_: str, borough_code: Optional[str] = None) -> list:
    """Return list of job dicts: {job_number, job_type, status, doc_links}.

    borough_code: numeric DOB borough code (1=MN, 2=BX, 3=BK, 4=QN, 5=SI).
    """
    if not bin_:
        log.warning("fetch_jobs_for_bin called with empty bin")
        return []

    sess = _session()
    # Primary entry: jobs by location keyed on BIN
    params = {"allbin": bin_}
    try:
        resp = http_utils.get(
            JOBS_FOR_BIN, params=params, session=sess, timeout=BIS_TIMEOUT
        )
    except Exception as exc:
        log.error("BIS jobs query failed for BIN %s: %s", bin_, exc)
        return []
    time.sleep(REQUEST_DELAY)

    jobs: list = []

    # BIS HTML is fragile (stray comments, unclosed tags) — use regex to
    # extract job number links rather than a real HTML parser.
    seen: set = set()
    for m in re.finditer(
        r'href="(JobsQueryByNumberServlet\?[^"]*passjobnumber=(\d{6,})[^"]*)"',
        resp.text,
    ):
        href = m.group(1).replace("&amp;", "&")
        job_number = m.group(2)
        if job_number in seen:
            continue
        seen.add(job_number)
        jobs.append(
            {
                "job_number": job_number,
                "job_url": urljoin(BIS_BASE, href),
                "source": "BIS",
                "doc_links": [],
            }
        )

    log.info("BIS found %d jobs for BIN %s", len(jobs), bin_)

    if len(jobs) > MAX_JOBS_TO_DETAIL:
        log.warning(
            "BIS returned %d jobs; capping detail fetch at %d",
            len(jobs),
            MAX_JOBS_TO_DETAIL,
        )
        jobs = jobs[:MAX_JOBS_TO_DETAIL]

    # Attempt job-detail scraping only for a small sample. BIS detail
    # pages sit behind an Akamai bot-manager WAF that returns 403 without
    # a JS-solved _abck cookie. We probe a few for evidence; the full
    # enumeration isn't worth the time.
    probe = jobs[: min(3, len(jobs))]
    for job in probe:
        try:
            dresp = http_utils.get(
                job["job_url"], session=sess, timeout=BIS_TIMEOUT
            )
            time.sleep(REQUEST_DELAY)
        except Exception as exc:
            log.info(
                "BIS job detail not scrapable %s (%s)", job["job_number"], exc
            )
            continue

        doc_links: list = []
        # BIS detail HTML is fragile; use regex extraction.
        for m in re.finditer(r'href="([^"]+)"', dresp.text):
            href = m.group(1)
            low = href.lower()
            if (
                ".pdf" in low
                or "scancode" in low
                or "scanview" in low
                or "documentinfo" in low
                or "pw1" in low
                or "tr1" in low
            ):
                doc_links.append(
                    {
                        "url": urljoin(BIS_BASE, href.replace("&amp;", "&")),
                        "label": "BIS document",
                        "source": "BIS",
                    }
                )
        job["doc_links"] = doc_links
        log.info(
            "BIS job %s: %d doc links", job["job_number"], len(doc_links)
        )

    return jobs
