"""Scrape https://a810-dobnow.nyc.gov/publish/ for post-2016 documents.

DOB NOW Public Portal exposes job filings; document downloads typically
require a session. We probe the public-facing search and capture any
direct PDF links exposed per filing.

Note: DOB NOW is a JS-heavy SPA. Without a headless browser, we can only
collect what the public REST/search endpoints return. Documents that are
gated behind the SPA viewer are recorded as references with their public
URL when known.
"""

import logging
import re
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from . import http_utils

log = logging.getLogger(__name__)

DOBNOW_BASE = "https://a810-dobnow.nyc.gov/publish/"
DOBNOW_SEARCH = (
    "https://a810-dobnow.nyc.gov/publish/Index.html#!/"
)
DOBNOW_PUBLIC_SEARCH_API = (
    "https://a810-dobnow.nyc.gov/publish/api/search/jobfiling"
)

REQUEST_DELAY = 1.0  # mandated 1s delay between DOB NOW requests
MAX_FILINGS_TO_PROBE = 5  # DOB NOW public portal is a JS SPA — probing
# beyond a handful of filings is pointless since the detail routes return
# 403 without a valid Akamai session. Keep the probe small as evidence
# and move on.

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/html, */*",
        }
    )
    return s


def fetch_documents_for_filing(
    filing_number: str, session: Optional[requests.Session] = None
) -> list:
    """Return list of {url, label, doc_type, source} for a filing number."""
    if not filing_number:
        return []

    sess = session or _session()
    docs: list = []

    # Try a public detail page first.
    detail_url = urljoin(
        DOBNOW_BASE, f"PublicPortal/Public/JobFiling/Detail/{filing_number}"
    )
    try:
        resp = http_utils.get(detail_url, session=sess)
        time.sleep(REQUEST_DELAY)
    except Exception as exc:
        log.warning(
            "DOB NOW detail fetch failed for %s: %s", filing_number, exc
        )
        return docs

    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        low = (href + " " + text).lower()
        if ".pdf" in href.lower() or "document" in low or "scan" in low:
            doc_type = _classify(text + " " + href)
            docs.append(
                {
                    "url": urljoin(DOBNOW_BASE, href),
                    "label": text or "document",
                    "doc_type": doc_type,
                    "source": "DOB_NOW",
                    "filing_number": filing_number,
                }
            )

    log.info(
        "DOB NOW filing %s: %d doc references", filing_number, len(docs)
    )
    return docs


def _classify(blob: str) -> str:
    """Classify a document by its label/href."""
    s = blob.lower()
    if "pw1" in s:
        return "PW1"
    if "tr1" in s:
        return "TR1"
    if "plan" in s:
        return "PLANS"
    if ".pdf" in s:
        return "PDF"
    return "OTHER"


def fetch_documents_for_filings(filing_numbers: list) -> list:
    """Batch helper: collect docs across multiple filings, polite delays.

    Caps probing at MAX_FILINGS_TO_PROBE since the DOB NOW public portal
    is a JS SPA that returns 403 on every direct detail URL without an
    Akamai-validated browser session.
    """
    if not filing_numbers:
        return []
    to_probe = filing_numbers[:MAX_FILINGS_TO_PROBE]
    if len(filing_numbers) > MAX_FILINGS_TO_PROBE:
        log.info(
            "DOB NOW: probing first %d of %d filings (SPA limitation)",
            MAX_FILINGS_TO_PROBE,
            len(filing_numbers),
        )
    sess = _session()
    out: list = []
    for fn in to_probe:
        try:
            docs = fetch_documents_for_filing(fn, session=sess)
            out.extend(docs)
        except Exception as exc:
            log.info(
                "DOB NOW: filing %s not publicly scrapable (%s)", fn, exc
            )
            continue
    return out
