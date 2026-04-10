"""proposal_generator entry point.

CLI:
    python3 -m proposal_generator.main \\
        --takeoff ./dob_output/<slug>/takeoff.json \\
        --contractor sanz_construction

Library:
    from proposal_generator.main import run_proposal
    pdf_path = run_proposal(takeoff_path=..., contractor="sanz_construction")
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from . import contractor_profile, pdf_builder

log = logging.getLogger("proposal_generator")


def _setup_logging(verbose: bool = True) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _address_slug(address: str) -> str:
    s = (address or "proposal").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")[:80]


def run_proposal(
    *,
    takeoff_path: Path,
    contractor: str,
    output_path: Path | None = None,
) -> Path:
    """Load takeoff + profile, render the bid PDF, return the output path."""
    takeoff_path = Path(takeoff_path)
    with open(takeoff_path) as fh:
        takeoff = json.load(fh)

    profile = contractor_profile.load_profile(contractor)

    if output_path is None:
        slug = _address_slug(takeoff.get("input_address") or takeoff_path.stem)
        output_path = Path("proposals") / f"{slug}_{contractor}_proposal.pdf"

    log.info("Rendering proposal for %s -> %s", contractor, output_path)
    pdf_builder.build_proposal_pdf(takeoff, profile, output_path)
    return output_path


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="proposal_generator",
        description="Turn a Sprint B takeoff.json into a bid proposal PDF.",
    )
    parser.add_argument("--takeoff", required=True)
    parser.add_argument("--contractor", default="sanz_construction")
    parser.add_argument("--output", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    _setup_logging(verbose=not args.quiet)
    try:
        path = run_proposal(
            takeoff_path=Path(args.takeoff),
            contractor=args.contractor,
            output_path=Path(args.output) if args.output else None,
        )
    except Exception as exc:
        log.exception("proposal_generator failed: %s", exc)
        return 2
    print(json.dumps({"proposal_pdf": str(path), "size_bytes": Path(path).stat().st_size}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
