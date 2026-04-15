"""Playwright-based scraper for BIS Certificate-of-Occupancy PDFs.

Sprint A without Playwright can reach the BIS Property Profile and
Jobs-by-Location pages, but the JobsQueryByNumberServlet (per-job
detail) is Akamai-blocked. However, the CO listing endpoint
`COsByLocationServlet?allbin={BIN}` is NOT Akamai-gated and exposes
one HTML <form> per downloadable CO PDF, each submitting a POST to
`CofoJobDocumentServlet`. Driving those forms with a real browser
yields real per-job PDFs from DOB — genuine Certificates of Occupancy
that contain floor count, height, occupancy group, and year data
that the takeoff_engine can use for real scope extraction.

This module is optional — it lazy-imports playwright so the rest of
dob_puller works fine without it. If Playwright is not installed,
`is_available()` returns False and calling the fetch function raises
a clear install hint.

Install:
    pip3 install --break-system-packages playwright
    python3 -m playwright install firefox
"""

import logging
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

BIS_LANDING = "https://a810-bisweb.nyc.gov/bisweb/bsqpm01.jsp"
COS_BY_LOCATION = (
    "https://a810-bisweb.nyc.gov/bisweb/COsByLocationServlet"
    "?requestid=0&allbin={bin_}"
)

REQUEST_DELAY = 1.0
DEFAULT_TIMEOUT_MS = 60_000
MAX_DOCS_PER_BIN = 20  # hard cap


def is_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def _require_playwright():
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        return sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run:\n"
            "  pip3 install --break-system-packages playwright\n"
            "  python3 -m playwright install firefox"
        ) from exc


def fetch_co_documents_for_bin(
    bin_: str,
    out_dir: Path,
    *,
    headless: bool = True,
    max_docs: int = MAX_DOCS_PER_BIN,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> list:
    """Drive BIS with a headless browser to download every CO PDF for a BIN.

    Returns a list of {url, label, doc_type, source, local_path,
    status, size_bytes, filing_number} dicts matching the format used
    by the rest of dob_puller.
    """
    sync_playwright = _require_playwright()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("Playwright BIS CO scrape starting for BIN %s", bin_)
    results: list = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=headless)
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            accept_downloads=True,
        )
        page = ctx.new_page()

        # Warm up cookies on the BIS landing page
        try:
            page.goto(
                BIS_LANDING, wait_until="domcontentloaded", timeout=timeout_ms
            )
            log.info("BIS landing OK: %s", page.title())
        except Exception as exc:
            log.error("BIS landing failed: %s", exc)
            browser.close()
            return results

        # Load CO listing for the BIN
        cos_url = COS_BY_LOCATION.format(bin_=bin_)
        try:
            page.goto(cos_url, wait_until="domcontentloaded", timeout=timeout_ms)
        except Exception as exc:
            log.error("CO listing fetch failed for BIN %s: %s", bin_, exc)
            browser.close()
            return results

        title = page.title()
        log.info("BIS CO listing page: %s", title)
        if "Access Denied" in title or "Error" in title:
            log.warning("BIS CO listing denied for BIN %s", bin_)
            browser.close()
            return results

        # Each downloadable PDF is a <form action="CofoJobDocumentServlet">
        # with inputs: bin, passcofonumber, requestid, cofomatadata1..5.
        form_descriptors: list = []
        forms = page.query_selector_all("form[action*='CofoJobDocumentServlet']")
        for f in forms:
            inputs = f.query_selector_all("input")
            data = {}
            for inp in inputs:
                n = inp.get_attribute("name") or ""
                v = inp.get_attribute("value") or ""
                if n:
                    data[n] = v
            pdf_name = data.get("passcofonumber") or data.get("cofomatadata5") or ""
            if pdf_name:
                form_descriptors.append((pdf_name, data))
        log.info(
            "BIS CO listing: %d downloadable PDFs for BIN %s",
            len(form_descriptors),
            bin_,
        )

        if not form_descriptors:
            browser.close()
            return results

        # Derive job_number per PDF: filenames that start with digits
        # look like "121183744-02.PDF" — take the leading digit run.
        import re as _re

        to_fetch = form_descriptors[:max_docs]
        for idx, (pdf_name, form_data) in enumerate(to_fetch, start=1):
            job_match = _re.match(r"(\d{6,})", pdf_name)
            job_number = job_match.group(1) if job_match else None
            try:
                # Re-load the listing page before each click — clicking a
                # link navigates away and invalidates the other anchors.
                page.goto(
                    cos_url, wait_until="domcontentloaded", timeout=timeout_ms
                )
                link = page.query_selector(f'a[href*="{pdf_name}"]')
                if not link:
                    log.warning("No anchor found for %s", pdf_name)
                    continue
                with page.expect_download(timeout=timeout_ms) as dinfo:
                    link.click()
                dl = dinfo.value
                # Preserve the real CO name rather than the servlet default
                safe = _re.sub(r"[^A-Za-z0-9._-]+", "_", pdf_name)
                save_path = out_dir / f"{idx:03d}_CO_{safe}"
                dl.save_as(str(save_path))
                size = save_path.stat().st_size
                log.info(
                    "Downloaded CO %s (%d bytes) via Playwright",
                    save_path.name,
                    size,
                )
                results.append(
                    {
                        "url": cos_url,
                        "label": pdf_name,
                        "doc_type": "CERTIFICATE_OF_OCCUPANCY",
                        "source": "BIS_PLAYWRIGHT",
                        "filing_number": job_number,
                        "status": "ok",
                        "local_path": str(save_path),
                        "size_bytes": size,
                    }
                )
            except Exception as exc:
                log.warning("Playwright CO download failed for %s: %s", pdf_name, exc)
                results.append(
                    {
                        "url": cos_url,
                        "label": pdf_name,
                        "doc_type": "CERTIFICATE_OF_OCCUPANCY",
                        "source": "BIS_PLAYWRIGHT",
                        "filing_number": job_number,
                        "status": "failed",
                        "reason": str(exc),
                    }
                )
            time.sleep(REQUEST_DELAY)

        browser.close()

    ok = sum(1 for r in results if r.get("status") == "ok")
    log.info(
        "Playwright BIS CO scrape done: %d/%d succeeded", ok, len(results)
    )
    return results
