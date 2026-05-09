"""Boolean-rule bucket analysis for DOB permits (no scoring).

Applies 6 independent boolean rules to every permit; a permit can land
in multiple buckets. Collapses owner + cost duplicates (e.g. Columbia
University filing the same $30M alteration against 4 campus buildings)
into single entries with a count note.

CLI:
    python3 -m permit_scanner.bucket_analyzer --borough MANHATTAN
"""

import argparse
import datetime
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

from . import socrata

log = logging.getLogger("bucket_analyzer")


# --- Boolean rules ---------------------------------------------------------

ROOF_RE = re.compile(r"roof", re.IGNORECASE)
EXCAVATE_RE = re.compile(r"excavat", re.IGNORECASE)
KITCHEN_RE = re.compile(
    r"kitchen|gut\s*reno|gut\s*renovation|interior\s*alteration|residential",
    re.IGNORECASE,
)
KITCHEN_JOB_TYPES = {"A2", "A3", "Alteration"}  # A2/A3 per DOB codes; Alteration as fallback
KITCHEN_BLDG_CLASSES = {"A", "B", "C", "D", "R"}  # residential classes

# In w9ak-ipjd the demolition job_type string is "Full Demolition", not
# "Demolition". We treat them as synonyms so the user-facing rule text
# ("job_type == Demolition") remains intuitive.
DEMO_TYPES = {"Demolition", "Full Demolition"}
ALTERATION_TYPES = {"Alteration"}
NEW_BUILDING_TYPES = {"New Building"}

# Super-set used for Socrata pull so New Building / Full Demolition rows
# are not excluded before the rules run.
ALL_RELEVANT_JOB_TYPES = (
    "Alteration",
    "Alteration CO",
    "ALT-CO - New Building with Existing Elements to Remain",
    "Demolition",
    "Full Demolition",
    "New Building",
)

# Combined helpers for bucket rules
ALT_OR_DEMO = ALTERATION_TYPES | DEMO_TYPES
ALT_DEMO_NB = ALTERATION_TYPES | DEMO_TYPES | NEW_BUILDING_TYPES


def _to_float(v) -> Optional[float]:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _description_blob(permit: dict) -> str:
    """Concatenate every work_type_ / building_type / description-ish field."""
    parts: list = []
    for k, v in permit.items():
        if not isinstance(v, str) or not v:
            continue
        kl = k.lower()
        if (
            "work_type" in kl
            or kl in ("job_description", "building_type")
        ):
            parts.append(v)
    return " ".join(parts)


def _address(permit: dict) -> str:
    hn = (permit.get("house_no") or "").strip()
    st = re.sub(r"\s+", " ", (permit.get("street_name") or "")).strip().title()
    bor = (permit.get("borough") or "").title()
    if hn and st:
        return f"{hn} {st}, {bor}".strip(", ")
    return bor or "(unknown address)"


def is_gc_opportunity(permit: dict) -> bool:
    applicant_last = (permit.get("applicant_last_name") or "").strip()
    filing_rep_biz = (permit.get("filing_representative_business_name") or "").strip()
    job_type = permit.get("job_type") or ""
    return (
        not applicant_last
        and not filing_rep_biz
        and job_type in ALT_DEMO_NB
    )


def is_abatement(permit: dict, *, pluto_by_bbl: dict) -> bool:
    job_type = permit.get("job_type") or ""
    if job_type not in ALT_OR_DEMO:
        return False
    bbl_key = str(permit.get("bbl", "")).split(".")[0]
    pluto = pluto_by_bbl.get(bbl_key) or {}
    year = pluto.get("year_built")
    return isinstance(year, int) and year < 1980


def is_concrete(permit: dict) -> bool:
    return (permit.get("job_type") or "") in NEW_BUILDING_TYPES


def is_demo(permit: dict) -> bool:
    return (permit.get("job_type") or "") in DEMO_TYPES


def is_roofing(permit: dict) -> bool:
    return bool(ROOF_RE.search(_description_blob(permit)))


def is_sitework(permit: dict) -> bool:
    if (permit.get("job_type") or "") in NEW_BUILDING_TYPES:
        return True
    return bool(EXCAVATE_RE.search(_description_blob(permit)))


def is_kitchen(permit: dict, *, pluto_by_bbl: dict) -> bool:
    """Residential kitchen renovation bucket.

    Matches if ALL of:
      - job_type is A2, A3, or Alteration
      - PLUTO bldgclass starts with A/B/C/D/R (residential)
      - permit cost between $10,000 and $200,000
    AND ANY of:
      - description contains a kitchen keyword
      - OR no description but type+class+cost all match (lower confidence)
    """
    job_type = (permit.get("job_type") or "").strip()
    # Check job_type — DOB uses "Alteration" for A2/A3 in most datasets
    if job_type not in KITCHEN_JOB_TYPES and job_type not in ALTERATION_TYPES:
        return False

    # Cost range check
    cost = _to_float(permit.get("initial_cost"))
    if cost is None or cost < 10_000 or cost > 200_000:
        return False

    # Building class check via PLUTO
    bbl_key = str(permit.get("bbl", "")).split(".")[0]
    pluto = pluto_by_bbl.get(bbl_key) or {}
    bldg_class = str(pluto.get("bldg_class") or "").strip().upper()
    if not bldg_class or bldg_class[0] not in KITCHEN_BLDG_CLASSES:
        return False

    # Keyword check — match if description has kitchen terms,
    # OR if no description available (still include at lower confidence)
    desc = _description_blob(permit)
    if desc.strip():
        return bool(KITCHEN_RE.search(desc))
    # No description — type+class+cost match is enough
    return True


BUCKETS: list = [
    ("GC_opportunity", is_gc_opportunity, False),
    ("Abatement", is_abatement, True),  # True => needs pluto_by_bbl
    ("Concrete", is_concrete, False),
    ("Demo", is_demo, False),
    ("Roofing", is_roofing, False),
    ("Sitework", is_sitework, False),
    ("Kitchen", is_kitchen, True),  # True => needs pluto_by_bbl
]


# --- Enrichment + clustering ----------------------------------------------


def _enriched(permit: dict, pluto_by_bbl: dict) -> dict:
    bbl_key = str(permit.get("bbl", "")).split(".")[0]
    pluto = pluto_by_bbl.get(bbl_key) or {}
    return {
        "job_filing_number": permit.get("job_filing_number"),
        "job_type": permit.get("job_type"),
        "address": _address(permit),
        "house_no": permit.get("house_no"),
        "street_name": permit.get("street_name"),
        "borough": permit.get("borough"),
        "bin": permit.get("bin"),
        "bbl": bbl_key or permit.get("bbl"),
        "initial_cost_usd": _to_float(permit.get("initial_cost")) or 0.0,
        "total_construction_floor_area_sqft": _to_float(
            permit.get("total_construction_floor_area")
        ),
        "owner_name": (
            (permit.get("owner_s_business_name") or "")
            or (
                f"{permit.get('owner_s_first_name','').strip()} "
                f"{permit.get('owner_s_last_name','').strip()}"
            ).strip()
            or None
        ),
        "filing_date": permit.get("filing_date"),
        "approved_date": permit.get("approved_date"),
        "year_built": pluto.get("year_built"),
        "bldg_area_sqft": pluto.get("bldg_area_sqft"),
        "num_floors": pluto.get("num_floors"),
        "applicant_last_name": permit.get("applicant_last_name"),
        "applicant_first_name": permit.get("applicant_first_name"),
        "applicant_license": permit.get("applicant_license"),
        "applicant_professional_title": permit.get("applicant_professional_title"),
        "filing_representative_business_name": permit.get(
            "filing_representative_business_name"
        ),
        "filing_representative_first_name": permit.get("filing_representative_first_name"),
        "filing_representative_last_name": permit.get("filing_representative_last_name"),
        "filing_representative_city": permit.get("filing_representative_city"),
        "filing_representative_state": permit.get("filing_representative_state"),
        "filing_representative_zip": permit.get("filing_representative_zip"),
    }


def _cluster_key(row: dict) -> Optional[tuple]:
    """Cluster identity = (normalized owner_name, initial_cost bucket).

    Rounds cost to nearest dollar to avoid float noise. Returns None if
    either field is missing so unclustered rows are passed through as-is.
    """
    owner = (row.get("owner_name") or "").strip().upper()
    cost = row.get("initial_cost_usd") or 0.0
    if not owner or cost <= 0:
        return None
    return (owner, round(cost, 0))


def cluster_dedupe(rows: list) -> list:
    """Collapse rows that share (owner_name, initial_cost).

    The representative row is the first encountered; a `cluster_size` and
    `cluster_addresses` list is attached. Non-clusterable rows pass
    through unchanged with cluster_size=1.
    """
    groups: dict = defaultdict(list)
    passthrough: list = []
    for r in rows:
        k = _cluster_key(r)
        if k is None:
            passthrough.append(r)
        else:
            groups[k].append(r)

    out: list = []
    for r in passthrough:
        out.append({**r, "cluster_size": 1, "cluster_addresses": [r["address"]]})
    for members in groups.values():
        rep = dict(members[0])
        addrs = [m["address"] for m in members]
        # Deduplicate addresses while preserving order
        seen: set = set()
        uniq_addrs = []
        for a in addrs:
            if a not in seen:
                seen.add(a)
                uniq_addrs.append(a)
        rep["cluster_size"] = len(members)
        rep["cluster_addresses"] = uniq_addrs
        rep["cluster_note"] = (
            f"{len(uniq_addrs)} buildings" if len(uniq_addrs) > 1 else None
        )
        out.append(rep)
    return out


# --- Bucket application ----------------------------------------------------


def apply_buckets(
    permits: list, *, pluto_by_bbl: dict
) -> dict:
    """Apply all 6 boolean rules and return per-bucket enriched rows."""
    results: dict = {name: [] for name, _, _ in BUCKETS}
    for p in permits:
        enriched = _enriched(p, pluto_by_bbl)
        for name, rule, needs_pluto in BUCKETS:
            if needs_pluto:
                if rule(p, pluto_by_bbl=pluto_by_bbl):
                    results[name].append(enriched)
            else:
                if rule(p):
                    results[name].append(enriched)
    return results


def summarize_bucket(name: str, rows: list) -> dict:
    """Produce per-bucket summary with clustered top-10 by initial_cost."""
    clustered = cluster_dedupe(rows)
    clustered.sort(key=lambda r: -(r.get("initial_cost_usd") or 0.0))
    top10 = clustered[:10]
    total_cost = sum(r.get("initial_cost_usd") or 0.0 for r in rows)
    return {
        "bucket": name,
        "count_raw": len(rows),
        "count_clustered": len(clustered),
        "total_initial_cost_usd": total_cost,
        "top_10": top10,
    }


# --- Printing --------------------------------------------------------------


def _fmt_money(v) -> str:
    try:
        return f"${float(v):,.0f}"
    except (TypeError, ValueError):
        return "—"


def print_bucket(summary: dict) -> None:
    print(f"\n=== {summary['bucket']} ===")
    print(f"  count:          {summary['count_raw']:,}")
    if summary["count_clustered"] != summary["count_raw"]:
        print(f"  after cluster:  {summary['count_clustered']:,}")
    print(f"  total value:    {_fmt_money(summary['total_initial_cost_usd'])}")
    print(f"  top 10 by initial_cost:")
    if not summary["top_10"]:
        print("    (none)")
        return
    print(
        f"    {'#':>3} {'Cost':>14} {'Year':>5} {'Job Type':<14} Address"
    )
    for i, r in enumerate(summary["top_10"], start=1):
        year = r.get("year_built") or "—"
        cost = _fmt_money(r.get("initial_cost_usd"))
        jt = (r.get("job_type") or "—")[:14]
        addr = r.get("address") or "—"
        note = r.get("cluster_note")
        suffix = f"  [{note}]" if note else ""
        print(
            f"    {i:>3} {cost:>14} {str(year):>5} {jt:<14} {addr}{suffix}"
        )
        if note and r.get("cluster_addresses"):
            extras = [a for a in r["cluster_addresses"] if a != r["address"]]
            for a in extras:
                print(f"         {'':>14} {'':>5} {'':<14}   ↳ {a}")


# --- Orchestration ---------------------------------------------------------


def run(
    *,
    borough: str = "MANHATTAN",
    days_back: int = 90,
    output_path: Path | None = None,
    limit: int | None = None,
) -> dict:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log.info("bucket_analyzer start: borough=%s days=%d", borough, days_back)

    permits = socrata.fetch_recent_permits(
        borough=borough,
        days_back=days_back,
        limit=limit,
        job_types=ALL_RELEVANT_JOB_TYPES,
    )
    total = len(permits)
    print(
        f"\nTotal {borough} permits pulled from DOB NOW (last {days_back} days): "
        f"{total:,}\n"
    )

    bbls = [p.get("bbl") for p in permits if p.get("bbl")]
    pluto_by_bbl = socrata.batch_lookup_pluto_year(bbls)
    log.info("PLUTO enriched: %d / %d BBLs", len(pluto_by_bbl), len(set(bbls)))

    per_bucket = apply_buckets(permits, pluto_by_bbl=pluto_by_bbl)
    summaries = [summarize_bucket(name, per_bucket[name]) for name, _, _ in BUCKETS]

    for s in summaries:
        print_bucket(s)

    scan_analysis = {
        "schema_version": "2.0",
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "borough": borough,
        "days_back": days_back,
        "permits_fetched": total,
        "pluto_enriched": len(pluto_by_bbl),
        "bucket_rules": {
            "GC_opportunity": "applicant_last_name empty AND filing_rep_business_name empty AND job_type in (Alteration, Demolition, New Building)",
            "Abatement": "year_built < 1980 AND job_type in (Alteration, Demolition)",
            "Concrete": "job_type == 'New Building'",
            "Demo": "job_type == 'Demolition' (matched as 'Full Demolition' in w9ak-ipjd)",
            "Roofing": "'roof' appears in any work_type_/description field (case-insensitive)",
            "Sitework": "job_type == 'New Building' OR 'excavat' appears in description",
            "Kitchen": "job_type in (A2, A3, Alteration) AND bldgclass starts with A/B/C/D/R AND cost $10K-$200K AND (kitchen keyword in description OR no description)",
        },
        "data_caveats": [
            "w9ak-ipjd work_type_* fields are binary flags ('0'/'1'/'Yes'/'No'), not free-text descriptions.",
            "There is no job_description column in w9ak-ipjd — only building_type is text (usually 'Other').",
            "Consequently the Roofing rule ('roof' in description) and the 'excavat' half of the Sitework rule will match near-zero in practice; the Sitework total is effectively driven by job_type == 'New Building'.",
            "DOB NOW labels demolition permits 'Full Demolition' — the Demo bucket treats that as synonymous with 'Demolition'.",
            "GC_opportunity (both applicant_last_name and filing_representative_business_name empty) is rare on DOB NOW filings because the applicant field is effectively required.",
        ],
        "buckets": summaries,
    }

    out = output_path or Path("scan_results") / f"scan_analysis_v2_{borough.lower()}_{datetime.date.today().isoformat()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        json.dump(scan_analysis, fh, indent=2, default=str)
    print(f"\nwrote {out}")
    return scan_analysis


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="permit_scanner.bucket_analyzer")
    parser.add_argument("--borough", default="MANHATTAN")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Cap rows pulled (0 = pull all via pagination).",
    )
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)
    try:
        run(
            borough=args.borough,
            days_back=args.days,
            limit=args.limit if args.limit and args.limit > 0 else None,
            output_path=Path(args.output) if args.output else None,
        )
    except Exception as exc:
        log.exception("bucket_analyzer failed: %s", exc)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
