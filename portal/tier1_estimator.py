"""Tier 1 instant deal-size estimator.

Computes a rough, formula-only deal size for every permit in
scan_results/scan_analysis_v2_*.json using PLUTO sqft + the bucket's trade
rate. No Vision calls, no document downloads, no Claude — pure arithmetic.

Output: tier1_cache.json at repo root, keyed by permit slug.

Schema::

    {
      "schema_version": "1.0",
      "generated_at": "<iso8601>",
      "source_scan": "<scan file name>",
      "permits": {
        "<slug>": {
          "slug": str,
          "address": str,
          "bucket": str,        # Abatement / Concrete / Demo / ...
          "sqft": float | null, # PLUTO bldg_area_sqft (fallback-aware)
          "sqft_source": "pluto" | "cost_proxy",
          "tier1_estimate_usd": float,
          "rate_per_sqft": float,
          "affected_pct": float,
          "permit_cost_usd": float | null,
          "year_built": int | null,
          "job_type": str | null,
          "initial_cost_usd": float | null,
          "neighborhood": str | null
        }
      }
    }

Tier 3 (Vision-run) takeoffs always win over Tier 1 in the UI; this cache is
purely a fallback for addresses that have not yet been through the full
pipeline.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_RESULTS_DIR = REPO_ROOT / "scan_results"
CACHE_PATH = REPO_ROOT / "tier1_cache.json"
SCHEMA_VERSION = "1.0"

# Bucket → rate card. Keys MUST match bucket names in scan_analysis_v2.
TIER1_RATES: dict[str, dict[str, float]] = {
    "Abatement":     {"rate_per_sqft": 10.00, "affected_pct": 0.15},
    "Demo":          {"rate_per_sqft": 8.50,  "affected_pct": 0.20},
    "Concrete":      {"rate_per_sqft": 22.00, "affected_pct": 0.12},
    "GC_opportunity":{"rate_per_sqft": 45.00, "affected_pct": 0.25},
    "Roofing":       {"rate_per_sqft": 18.00, "affected_pct": 0.08},
    "Sitework":      {"rate_per_sqft": 12.00, "affected_pct": 0.10},
}
MARKUP = 1.22
COST_PROXY_RATIO = 0.35  # when PLUTO sqft is missing


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify_address(address: str) -> str:
    s = (address or "").lower().strip()
    for ch in [",", ".", "'", '"']:
        s = s.replace(ch, "")
    return "_".join(s.split())


def _latest_scan_path() -> Path | None:
    if not SCAN_RESULTS_DIR.exists():
        return None
    candidates = sorted(
        SCAN_RESULTS_DIR.glob("scan_analysis_v2_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def estimate_permit(permit: dict[str, Any], bucket: str) -> dict[str, Any] | None:
    """Compute a Tier 1 estimate for a single permit row.

    Returns ``None`` if the bucket is unrecognised (no rate card).
    """
    rates = TIER1_RATES.get(bucket)
    if rates is None:
        return None

    rate = rates["rate_per_sqft"]
    pct = rates["affected_pct"]

    sqft_raw = permit.get("bldg_area_sqft")
    try:
        sqft = float(sqft_raw) if sqft_raw not in (None, "") else None
    except (TypeError, ValueError):
        sqft = None

    cost_raw = permit.get("initial_cost_usd")
    try:
        permit_cost = float(cost_raw) if cost_raw not in (None, "") else None
    except (TypeError, ValueError):
        permit_cost = None

    if sqft and sqft > 0:
        estimate = sqft * rate * pct * MARKUP
        sqft_source = "pluto"
    elif permit_cost and permit_cost > 0:
        estimate = permit_cost * COST_PROXY_RATIO
        sqft_source = "cost_proxy"
    else:
        # Nothing to work with — skip rather than emit a bogus zero.
        return None

    address = permit.get("address") or ""
    return {
        "slug": _slugify_address(address),
        "address": address,
        "bucket": bucket,
        "sqft": sqft,
        "sqft_source": sqft_source,
        "tier1_estimate_usd": round(estimate, 2),
        "rate_per_sqft": rate,
        "affected_pct": pct,
        "permit_cost_usd": permit_cost,
        "year_built": permit.get("year_built"),
        "job_type": permit.get("job_type"),
        "initial_cost_usd": permit_cost,
        "neighborhood": permit.get("neighborhood") or permit.get("borough"),
    }


def build_cache(scan_path: Path | None = None) -> dict[str, Any]:
    """Scan the latest scan_analysis_v2 file and produce the Tier 1 cache."""
    scan_path = scan_path or _latest_scan_path()
    if scan_path is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": _now_iso(),
            "source_scan": None,
            "permits": {},
        }

    with open(scan_path) as f:
        scan = json.load(f)

    permits: dict[str, dict[str, Any]] = {}
    for bucket in scan.get("buckets", []):
        name = bucket.get("bucket")
        # top_10 is what the portal surfaces; it's also all that's persisted
        # per bucket in scan_analysis_v2. Run estimate on every row.
        for permit in bucket.get("top_10") or []:
            est = estimate_permit(permit, name)
            if est is None:
                continue
            slug = est["slug"]
            # If the same address shows up in multiple buckets, keep the
            # highest-value estimate — that's what Nauman cares about.
            existing = permits.get(slug)
            if existing is None or est["tier1_estimate_usd"] > existing["tier1_estimate_usd"]:
                permits[slug] = est

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "source_scan": scan_path.name,
        "permits": permits,
    }


def load_cache() -> dict[str, Any]:
    if not CACHE_PATH.exists():
        return {"schema_version": SCHEMA_VERSION, "permits": {}}
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"schema_version": SCHEMA_VERSION, "permits": {}}


def save_cache(cache: dict[str, Any]) -> None:
    tmp = CACHE_PATH.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(cache, f, indent=2)
    tmp.replace(CACHE_PATH)


def refresh_cache() -> dict[str, Any]:
    cache = build_cache()
    save_cache(cache)
    return cache


def bucket_totals(cache: dict[str, Any] | None = None) -> dict[str, dict[str, float]]:
    """Aggregate Tier 1 totals per bucket for the dashboard.

    Returns ``{bucket: {"count": n, "total_usd": x}}``.
    """
    cache = cache or load_cache()
    out: dict[str, dict[str, float]] = {}
    for entry in cache.get("permits", {}).values():
        b = entry.get("bucket", "unknown")
        row = out.setdefault(b, {"count": 0, "total_usd": 0.0})
        row["count"] += 1
        row["total_usd"] += float(entry.get("tier1_estimate_usd") or 0)
    return out


if __name__ == "__main__":
    cache = refresh_cache()
    n = len(cache.get("permits", {}))
    src = cache.get("source_scan")
    totals = bucket_totals(cache)
    grand = sum(row["total_usd"] for row in totals.values())
    print(f"tier1_cache.json written ({n} permits from {src})")
    for bucket, row in sorted(totals.items()):
        print(f"  {bucket:<16} {int(row['count']):>4}  ${row['total_usd']:>15,.0f}")
    print(f"  {'TOTAL':<16} {n:>4}  ${grand:>15,.0f}")
