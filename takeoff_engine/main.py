"""takeoff_engine entry point.

CLI:
    python3 -m takeoff_engine.main \\
        --input ./dob_output/280_park_avenue_manhattan/result.json \\
        --contractor sanz_construction \\
        --trades abatement,concrete,demo

Library:
    from takeoff_engine.main import run_takeoff
    takeoff = run_takeoff(input_json=..., contractor=..., trades=[...])
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from . import (
    document_classifier,
    quantity_estimator,
    scope_parser,
    takeoff_builder,
    vision_extractor,
)

log = logging.getLogger("takeoff_engine")

DEFAULT_TRADES = ["abatement", "concrete", "demo"]


def _setup_logging(verbose: bool = True) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _resolve_pdf_paths(sprint_a_result: dict, input_json_path: Path) -> list:
    """Walk the Sprint A result.json and return absolute PDF paths."""
    downloads = (
        sprint_a_result.get("documents", {}).get("downloaded", []) or []
    )
    out: list = []
    base_dir = input_json_path.parent  # .../dob_output/<slug>/
    for d in downloads:
        if d.get("status") != "ok":
            continue
        p = Path(d.get("local_path", ""))
        if not p.is_absolute():
            p = (base_dir.parent.parent / p).resolve()
        if p.exists():
            out.append(p)
        else:
            # Try resolving relative to input JSON directory
            alt = (base_dir / p.name).resolve()
            if alt.exists():
                out.append(alt)
    return out


def run_takeoff(
    *,
    input_json: Path,
    contractor: str,
    trades: list,
    output_path: Path | None = None,
    max_pages_per_pdf: int = 2,
    skip_vision: bool = False,
) -> dict:
    """Run the full takeoff pipeline.

    Returns the final takeoff dict (also written to disk).
    """
    input_json = Path(input_json)
    log.info("=== takeoff_engine start: %s ===", input_json)

    with open(input_json) as fh:
        sprint_a_result = json.load(fh)

    pdf_paths = _resolve_pdf_paths(sprint_a_result, input_json)
    log.info("Found %d downloaded PDFs", len(pdf_paths))

    classifications: list = []
    vision_pages: list = []
    if pdf_paths and not skip_vision:
        classifications = document_classifier.classify_all(
            pdf_paths, max_pages=max_pages_per_pdf
        )
        vision_pages = vision_extractor.extract_all(classifications)
    else:
        log.warning("Skipping Vision (no PDFs or skip_vision=True)")

    price_sheet = quantity_estimator.load_price_sheet(contractor)

    scope = scope_parser.build_scope(
        trades,
        permits=sprint_a_result.get("permits", {}),
        vision_pages=vision_pages,
    )
    priced = quantity_estimator.price_scope(scope, price_sheet, trades)
    takeoff = takeoff_builder.build_takeoff(
        sprint_a_result=sprint_a_result,
        contractor=contractor,
        trades=trades,
        classifications=classifications,
        vision_pages=vision_pages,
        scope=scope,
        priced=priced,
    )

    if output_path is None:
        output_path = input_json.parent / "takeoff.json"
    takeoff_builder.write_takeoff(takeoff, output_path)

    applicable_count = sum(1 for t in takeoff["trades"] if t["applicable"])
    log.info(
        "=== takeoff_engine done: %d trades assessed, %d applicable, total=$%s ===",
        len(takeoff["trades"]),
        applicable_count,
        takeoff["estimated_total_cost"].get("total"),
    )
    return takeoff


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="takeoff_engine",
        description="Turn Sprint A DOB result.json + PDFs into a draft takeoff.",
    )
    parser.add_argument("--input", required=True, help="Sprint A result.json path")
    parser.add_argument("--contractor", default="sanz_construction")
    parser.add_argument(
        "--trades",
        default=",".join(DEFAULT_TRADES),
        help="Comma-separated trade list",
    )
    parser.add_argument("--output", default=None, help="takeoff.json output path")
    parser.add_argument("--max-pages-per-pdf", type=int, default=2)
    parser.add_argument(
        "--skip-vision",
        action="store_true",
        help="Skip Claude Vision calls (useful for dry runs).",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    _setup_logging(verbose=not args.quiet)
    trades = [t.strip() for t in args.trades.split(",") if t.strip()]

    try:
        takeoff = run_takeoff(
            input_json=Path(args.input),
            contractor=args.contractor,
            trades=trades,
            output_path=Path(args.output) if args.output else None,
            max_pages_per_pdf=args.max_pages_per_pdf,
            skip_vision=args.skip_vision,
        )
    except Exception as exc:
        log.exception("takeoff_engine failed: %s", exc)
        return 2

    summary = {
        "contractor": args.contractor,
        "trades_assessed": [t["name"] for t in takeoff["trades"]],
        "trades_applicable": [
            t["name"] for t in takeoff["trades"] if t["applicable"]
        ],
        "estimated_total_cost": takeoff["estimated_total_cost"].get("total"),
        "flag_count": len(takeoff["flags"]),
        "scope_summary": takeoff["scope_summary"],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
