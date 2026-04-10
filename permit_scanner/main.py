"""permit_scanner entry point.

CLI:
    python3 -m permit_scanner.main --borough MANHATTAN --top 5 --auto-run

Queries the DOB NOW Build approved permits dataset for recent
Alteration / Demolition filings in the given borough, scores each for
Sanz fit, ranks, and (optionally) runs the full dob_puller →
takeoff_engine → proposal_generator → outreach_engine pipeline for
the top N.
"""

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path

from . import pipeline_runner, scorer, socrata

log = logging.getLogger("permit_scanner")


def _setup_logging(verbose: bool = True) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run_scan(
    *,
    borough: str = "MANHATTAN",
    days_back: int = 90,
    limit: int = 1000,
    min_score: int = 50,
    top_n: int = 20,
    auto_run_top: int = 0,
    contractor: str = "sanz_construction",
    trades: list | None = None,
    use_playwright: bool = True,
    output_path: Path | None = None,
) -> dict:
    """Run the scan pipeline end-to-end and return the scan_results dict."""
    if trades is None:
        trades = ["abatement", "concrete", "demo"]

    log.info(
        "scan start: borough=%s days_back=%d limit=%d top_n=%d auto_run=%d",
        borough,
        days_back,
        limit,
        top_n,
        auto_run_top,
    )
    permits = socrata.fetch_recent_permits(
        borough=borough, days_back=days_back, limit=limit
    )
    log.info("raw permits fetched: %d", len(permits))

    # Enrich with PLUTO year (for +30 abatement rule)
    bbls = [p.get("bbl") for p in permits if p.get("bbl")]
    pluto_by_bbl = socrata.batch_lookup_pluto_year(bbls)

    ranked = scorer.rank_permits(
        permits,
        pluto_by_bbl=pluto_by_bbl,
        min_score=min_score,
        top_n=top_n,
    )
    log.info("ranked (score >= %d): %d", min_score, len(ranked))

    auto_run_results: list = []
    if auto_run_top and ranked:
        targets = ranked[: min(auto_run_top, len(ranked))]
        log.info("auto-running full pipeline on top %d", len(targets))
        for i, row in enumerate(targets, start=1):
            log.info(
                "--- pipeline %d/%d: %s (score=%d) ---",
                i,
                len(targets),
                row["address"],
                row["score"],
            )
            try:
                artifacts = pipeline_runner.run_full_pipeline(
                    row,
                    contractor=contractor,
                    trades=trades,
                    use_playwright=use_playwright,
                )
            except Exception as exc:
                log.exception("pipeline exception for %s: %s", row["address"], exc)
                artifacts = {
                    "address": row["address"],
                    "error": str(exc),
                }
            auto_run_results.append(artifacts)

    scan_results = {
        "schema_version": "1.0",
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "borough": borough,
        "days_back": days_back,
        "query_limit": limit,
        "min_score": min_score,
        "top_n": top_n,
        "contractor": contractor,
        "trades": trades,
        "permits_fetched": len(permits),
        "pluto_enriched": len(pluto_by_bbl),
        "ranked_count": len(ranked),
        "ranked": ranked,
        "auto_run_top": auto_run_top,
        "auto_run_results": auto_run_results,
    }

    out = output_path or Path("scan_results") / f"{borough.lower()}_{datetime.date.today().isoformat()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        json.dump(scan_results, fh, indent=2, default=str)
    log.info("wrote scan_results to %s", out)

    return {"path": str(out), "scan": scan_results}


def _print_summary(scan: dict) -> None:
    print("\n=== PERMIT SCAN SUMMARY ===")
    print(f"Borough:          {scan['borough']}")
    print(f"Window:           last {scan['days_back']} days")
    print(f"Permits fetched:  {scan['permits_fetched']}")
    print(f"PLUTO enriched:   {scan['pluto_enriched']}")
    print(f"Ranked (>= {scan['min_score']}):  {scan['ranked_count']}")
    print()
    print(f"--- Top {min(len(scan['ranked']), 10)} ranked permits ---")
    for i, r in enumerate(scan["ranked"][:10], start=1):
        cost = r.get("initial_cost_usd")
        cost_str = f"${cost:,.0f}" if cost else "—"
        yr = r.get("year_built") or "—"
        print(
            f"  {i:>2}. score={r['score']:>3}  {r['address'][:60]:60s}  "
            f"type={r.get('job_type_code','?'):6s} cost={cost_str:>14s} yr={yr}"
        )

    if scan.get("auto_run_results"):
        print()
        print(f"--- Auto-run results ({len(scan['auto_run_results'])}) ---")
        for i, ar in enumerate(scan["auto_run_results"], start=1):
            total = ar.get("estimated_total_cost")
            total_str = f"${total:,.0f}" if total else "—"
            status = "ok"
            for ek in ("dob_puller_error", "takeoff_engine_error", "proposal_error", "outreach_error", "error"):
                if ar.get(ek):
                    status = f"FAIL @ {ek}: {ar[ek][:40]}"
                    break
            print(f"  {i}. {ar['address'][:60]:60s} total={total_str:>14s}  {status}")
            if ar.get("proposal_pdf"):
                print(f"       proposal: {ar['proposal_pdf']}")


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="permit_scanner",
        description="Scan DOB permits for Sanz-fit opportunities and optionally run the full pipeline.",
    )
    parser.add_argument("--borough", default="MANHATTAN")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--min-score", type=int, default=50)
    parser.add_argument("--top", type=int, default=20, help="Top-N to include in ranked output")
    parser.add_argument(
        "--auto-run",
        nargs="?",
        const=5,
        type=int,
        default=0,
        help="Auto-run full pipeline on top N permits (default 5 when flag bare)",
    )
    parser.add_argument("--contractor", default="sanz_construction")
    parser.add_argument("--trades", default="abatement,concrete,demo")
    parser.add_argument("--no-playwright", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    _setup_logging(verbose=not args.quiet)
    trades = [t.strip() for t in args.trades.split(",") if t.strip()]

    try:
        result = run_scan(
            borough=args.borough,
            days_back=args.days,
            limit=args.limit,
            min_score=args.min_score,
            top_n=args.top,
            auto_run_top=args.auto_run,
            contractor=args.contractor,
            trades=trades,
            use_playwright=not args.no_playwright,
            output_path=Path(args.output) if args.output else None,
        )
    except Exception as exc:
        log.exception("permit_scanner failed: %s", exc)
        return 2

    _print_summary(result["scan"])
    print(f"\nscan_results: {result['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
