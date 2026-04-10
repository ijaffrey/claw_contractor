"""Download PDFs from DOB sources, with retries and priority ordering.

Priority for download (per sprint brief):
  1. PW1 (plan/work application)
  2. TR1
  3. Plan sets
  4. Everything else
"""

import hashlib
import logging
import re
import time
from pathlib import Path
from typing import Optional

import requests

log = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_SECONDS = 2.0
TIMEOUT = 60
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

PRIORITY_ORDER = {"PW1": 0, "TR1": 1, "PLANS": 2, "PDF": 3, "OTHER": 4}


def classify_doc(label: str, url: str) -> str:
    """Best-effort doc type classification."""
    s = (label + " " + url).lower()
    if "pw1" in s or "plan/work" in s or "work application" in s:
        return "PW1"
    if "tr1" in s:
        return "TR1"
    if "plan" in s and "application" not in s:
        return "PLANS"
    if ".pdf" in s:
        return "PDF"
    return "OTHER"


def sort_by_priority(docs: list) -> list:
    """Sort doc dicts so PW1 comes first, etc."""
    def key(d: dict) -> int:
        dt = d.get("doc_type") or classify_doc(
            d.get("label", ""), d.get("url", "")
        )
        return PRIORITY_ORDER.get(dt, 99)

    return sorted(docs, key=key)


def _safe_filename(doc: dict, idx: int) -> str:
    label = doc.get("label") or "document"
    label = re.sub(r"[^A-Za-z0-9._-]+", "_", label)[:60]
    url = doc.get("url", "")
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    doc_type = doc.get("doc_type") or "DOC"
    suffix = ".pdf" if ".pdf" in url.lower() else ".bin"
    return f"{idx:03d}_{doc_type}_{label}_{h}{suffix}"


def download_one(
    doc: dict,
    out_dir: Path,
    idx: int,
    *,
    session: Optional[requests.Session] = None,
) -> dict:
    """Download a single doc with retries. Returns status dict."""
    sess = session or requests.Session()
    sess.headers.setdefault("User-Agent", USER_AGENT)

    url = doc.get("url")
    if not url:
        return {**doc, "status": "skipped", "reason": "no_url"}

    out_dir.mkdir(parents=True, exist_ok=True)
    fname = _safe_filename(doc, idx)
    fpath = out_dir / fname

    last_err: Optional[str] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info("Downloading %s (attempt %d)", url, attempt)
            r = sess.get(url, timeout=TIMEOUT, stream=True)
            if r.status_code == 503:
                last_err = "503"
                log.warning("503 on %s, retrying", url)
                time.sleep(BACKOFF_SECONDS * attempt)
                continue
            if r.status_code in (401, 403, 404):
                last_err = f"http_{r.status_code}"
                log.info("HTTP %s on %s (terminal)", r.status_code, url)
                break
            if r.status_code != 200:
                last_err = f"http_{r.status_code}"
                log.warning("HTTP %s on %s", r.status_code, url)
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_SECONDS * attempt)
                    continue
                break
            with open(fpath, "wb") as fh:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
            size = fpath.stat().st_size
            log.info("Saved %s (%d bytes)", fpath, size)
            return {
                **doc,
                "status": "ok",
                "local_path": str(fpath),
                "size_bytes": size,
            }
        except requests.RequestException as exc:
            last_err = str(exc)
            log.warning("Download error %s: %s", url, exc)
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_SECONDS * attempt)

    return {**doc, "status": "failed", "reason": last_err or "unknown"}


def download_documents(docs: list, out_dir: Path) -> list:
    """Download a list of docs in priority order. Never crash on one failure."""
    if not docs:
        log.info("No documents to download")
        return []

    ordered = sort_by_priority(docs)
    sess = requests.Session()
    sess.headers["User-Agent"] = USER_AGENT

    results: list = []
    for i, doc in enumerate(ordered, start=1):
        try:
            res = download_one(doc, out_dir, i, session=sess)
        except Exception as exc:
            log.error("Unexpected error downloading %s: %s", doc.get("url"), exc)
            res = {**doc, "status": "failed", "reason": f"exception: {exc}"}
        results.append(res)

    ok = sum(1 for r in results if r.get("status") == "ok")
    log.info("Downloaded %d/%d documents", ok, len(results))
    return results
