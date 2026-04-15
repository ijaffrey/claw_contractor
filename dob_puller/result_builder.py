"""Assemble the final result.json from all pipeline outputs."""

import datetime
import json
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)


def address_slug(address: str) -> str:
    """Filesystem-safe slug for an address."""
    s = address.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:80]


def extract_filing_numbers(permits: dict) -> list:
    """Pull DOB NOW filing numbers from job_filings + approved_permits."""
    out: set = set()
    for row in permits.get("job_filings", []) or []:
        for k in ("job_filing_number", "filing_number", "job__"):
            v = row.get(k)
            if v:
                out.add(str(v))
                break
    for row in permits.get("approved_permits", []) or []:
        for k in ("job_filing_number", "filing_number", "job__"):
            v = row.get(k)
            if v:
                out.add(str(v))
                break
    return sorted(out)


def build_result(
    address: str,
    resolved: dict | None,
    permits: dict,
    bis_jobs: list,
    dobnow_docs: list,
    download_results: list,
) -> dict:
    """Construct the final result dict."""
    return {
        "schema_version": "1.0",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "input_address": address,
        "resolved": resolved or {},
        "permits": {
            "dob_now_job_filings": permits.get("job_filings", []),
            "dob_now_approved_permits": permits.get("approved_permits", []),
            "dob_now_build_approved_apps": permits.get("build_approved_apps", []),
            "bis_jobs": bis_jobs,
        },
        "documents": {
            "dob_now": dobnow_docs,
            "downloaded": download_results,
        },
        "summary": {
            "job_filing_count": len(permits.get("job_filings", []) or []),
            "approved_permit_count": len(
                permits.get("approved_permits", []) or []
            ),
            "build_approved_apps_count": len(
                permits.get("build_approved_apps", []) or []
            ),
            "bis_job_count": len(bis_jobs or []),
            "documents_referenced": (len(dobnow_docs or []))
            + sum(len(j.get("doc_links") or []) for j in (bis_jobs or [])),
            "documents_downloaded": sum(
                1 for d in (download_results or []) if d.get("status") == "ok"
            ),
        },
    }


def write_result(result: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "result.json"
    with open(path, "w") as fh:
        json.dump(result, fh, indent=2, default=str)
    log.info("Wrote %s", path)
    return path
