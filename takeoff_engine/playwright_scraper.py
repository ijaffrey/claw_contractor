"""Optional Playwright-based scraper for Akamai-protected DOB pages.

Sprint A discovered that a810-bisweb.nyc.gov and a810-dobnow.nyc.gov
publish detail pages sit behind an Akamai Bot Manager that returns 403
on every direct HTTP request without a JavaScript-solved `_abck`
cookie. A headless browser can drive those pages, let Akamai fingerprint
it, and then download real per-job PDFs.

This module is OPTIONAL — it lazy-imports playwright so that the rest
of takeoff_engine works fine without it. If Playwright isn't installed,
`is_available()` returns False and the module's functions raise a
clear error if called.

Install:
    pip3 install --break-system-packages playwright
    python3 -m playwright install chromium
"""

import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


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
            "  python3 -m playwright install chromium"
        ) from exc


def fetch_bis_job_documents(
    bin_: str,
    job_number: str,
    out_dir: Path,
    *,
    headless: bool = True,
    timeout_ms: int = 60000,
) -> list:
    """Use a real browser to open a BIS job detail page and download any
    linked documents.

    Returns a list of {url, local_path, source} dicts for downloaded
    documents. This is a stub scaffold — it launches the browser and
    navigates the BIS job page, but does not yet walk every possible
    document type. Intended to be hardened incrementally once
    Playwright is installed.
    """
    sync_playwright = _require_playwright()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(
            accept_downloads=True,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()
        # Warm up cookies by hitting the BIN location first
        page.goto(
            f"https://a810-bisweb.nyc.gov/bisweb/JobsQueryByLocationServlet?allbin={bin_}",
            timeout=timeout_ms,
        )
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        # Then the job detail page
        detail_url = (
            "https://a810-bisweb.nyc.gov/bisweb/JobsQueryByNumberServlet"
            f"?requestid=0&passjobnumber={job_number}&passdocnumber=01"
        )
        try:
            page.goto(detail_url, timeout=timeout_ms)
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception as exc:
            log.warning("BIS detail load failed for %s: %s", job_number, exc)
            browser.close()
            return results

        # Look for any links that look like documents
        anchors = page.query_selector_all("a[href]")
        for a in anchors:
            try:
                href: Optional[str] = a.get_attribute("href")
            except Exception:
                continue
            if not href:
                continue
            low = href.lower()
            if ".pdf" in low or "scancode" in low or "documentinfo" in low:
                results.append(
                    {
                        "url": href if href.startswith("http")
                        else f"https://a810-bisweb.nyc.gov/bisweb/{href}",
                        "source": "BIS_PLAYWRIGHT",
                        "job_number": job_number,
                    }
                )
        browser.close()
    log.info(
        "Playwright BIS scrape: %d doc links for job %s", len(results), job_number
    )
    return results
