"""dob_puller entry point.

CLI:
    python3 -m dob_puller.main "280 Park Avenue, Manhattan"

Library:
    from dob_puller.main import run_dob_pull
    result = run_dob_pull("280 Park Avenue, Manhattan")
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from . import (
    address_resolver,
    bis_scraper,
    dobnow_scraper,
    document_downloader,
    permit_fetcher,
    reference_forms,
    result_builder,
)

log = logging.getLogger("dob_puller")


def _setup_logging(verbose: bool = True) -> None:
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run_dob_pull(
    address_or_job_number: str,
    *,
    output_root: Path | None = None,
) -> dict:
    """Pull all DOB metadata + documents for an address (or job number).

    Returns the result dict (also written to result.json on disk).
    """
    out_root = output_root or Path("dob_output")
    slug = result_builder.address_slug(address_or_job_number)
    addr_dir = out_root / slug
    docs_dir = addr_dir / "docs"

    log.info("=== dob_puller start: %s ===", address_or_job_number)
    log.info("Output dir: %s", addr_dir)

    # Step 1: resolve address -> BIN/BBL
    resolved = None
    if not address_or_job_number.isdigit():
        try:
            resolved = address_resolver.resolve_address(address_or_job_number)
        except Exception as exc:
            log.error("Address resolution failed: %s", exc)
            resolved = None
    else:
        log.info("Input looks like a job number, skipping address resolve")

    # Step 2: fetch DOB NOW permits
    permits = {"job_filings": [], "approved_permits": []}
    if resolved:
        try:
            permits = permit_fetcher.fetch_all_permits(resolved)
        except Exception as exc:
            log.error("Permit fetch failed: %s", exc)

    # Step 3: scrape BIS for legacy jobs + docs
    bis_jobs: list = []
    if resolved and resolved.get("bin"):
        try:
            bis_jobs = bis_scraper.fetch_jobs_for_bin(resolved["bin"])
        except Exception as exc:
            log.error("BIS scrape failed: %s", exc)

    # Step 4: collect DOB NOW document references
    filing_numbers = result_builder.extract_filing_numbers(permits)
    dobnow_docs: list = []
    if filing_numbers:
        try:
            dobnow_docs = dobnow_scraper.fetch_documents_for_filings(
                filing_numbers
            )
        except Exception as exc:
            log.error("DOB NOW doc scrape failed: %s", exc)

    # Step 5: download in priority order
    all_docs: list = []
    # Reference DOB form templates — guaranteed-downloadable baseline
    all_docs.extend(reference_forms.get_reference_forms())
    all_docs.extend(dobnow_docs)
    for j in bis_jobs:
        for d in j.get("doc_links") or []:
            all_docs.append(
                {
                    "url": d["url"],
                    "label": d.get("label", ""),
                    "doc_type": document_downloader.classify_doc(
                        d.get("label", ""), d["url"]
                    ),
                    "source": "BIS",
                    "filing_number": j.get("job_number"),
                }
            )
    download_results = document_downloader.download_documents(
        all_docs, docs_dir
    )

    # Step 6: build + write result
    result = result_builder.build_result(
        address=address_or_job_number,
        resolved=resolved,
        permits=permits,
        bis_jobs=bis_jobs,
        dobnow_docs=dobnow_docs,
        download_results=download_results,
    )
    result_builder.write_result(result, addr_dir)

    log.info(
        "=== dob_puller done: %d filings, %d permits, %d docs downloaded ===",
        result["summary"]["job_filing_count"],
        result["summary"]["approved_permit_count"],
        result["summary"]["documents_downloaded"],
    )
    return result


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dob_puller",
        description="Pull NYC DOB permit metadata + documents for an address.",
    )
    parser.add_argument(
        "address",
        help="Address (e.g. '280 Park Avenue, Manhattan') or job number",
    )
    parser.add_argument(
        "--output-root",
        default="dob_output",
        help="Output directory root (default: dob_output)",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    _setup_logging(verbose=not args.quiet)
    try:
        result = run_dob_pull(
            args.address, output_root=Path(args.output_root)
        )
    except Exception as exc:
        log.exception("dob_puller failed: %s", exc)
        return 2

    print(
        json.dumps(
            {
                "address": args.address,
                "summary": result["summary"],
                "output_dir": str(Path(args.output_root) / result_builder.address_slug(args.address)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
