"""Resolve a NYC address to BIN/BBL via NYC Open Data.

No Geoclient API key required. Uses the Building Footprints / PLUTO datasets
on Socrata with fuzzy matching on house number + street name + borough.
"""

import logging
import re
from typing import Optional

from . import http_utils

log = logging.getLogger(__name__)

# PLUTO dataset (current). Has bbl, address, borough, zipcode (no bin).
PLUTO_ENDPOINT = "https://data.cityofnewyork.us/resource/64uk-42ks.json"
# Building Footprints — used to resolve BIN from BBL.
BUILDING_FOOTPRINTS_ENDPOINT = (
    "https://data.cityofnewyork.us/resource/5zhs-2jue.json"
)

BOROUGH_NAMES = {
    "manhattan": "MN",
    "mn": "MN",
    "bronx": "BX",
    "bx": "BX",
    "brooklyn": "BK",
    "bk": "BK",
    "queens": "QN",
    "qn": "QN",
    "staten island": "SI",
    "si": "SI",
}

STREET_SUFFIX_NORMALIZE = {
    "street": "ST",
    "st": "ST",
    "avenue": "AVENUE",
    "ave": "AVENUE",
    "av": "AVENUE",
    "road": "ROAD",
    "rd": "ROAD",
    "boulevard": "BOULEVARD",
    "blvd": "BOULEVARD",
    "place": "PLACE",
    "pl": "PLACE",
    "drive": "DRIVE",
    "dr": "DRIVE",
    "lane": "LANE",
    "ln": "LANE",
    "court": "COURT",
    "ct": "COURT",
    "parkway": "PARKWAY",
    "pkwy": "PARKWAY",
    "square": "SQUARE",
    "sq": "SQUARE",
    "terrace": "TERRACE",
    "ter": "TERRACE",
}


def parse_address(address: str) -> dict:
    """Split a free-form NYC address into components.

    Returns dict with house_number, street, borough (code), normalized.
    """
    raw = address.strip()
    parts = [p.strip() for p in raw.split(",")]
    street_part = parts[0] if parts else raw
    borough_part = parts[1] if len(parts) > 1 else ""

    # House number = leading digits (with optional dash, e.g. 123-45)
    m = re.match(r"^\s*([\d\-]+)\s+(.+)$", street_part)
    if not m:
        raise ValueError(f"Could not parse house number from: {street_part!r}")
    house_number = m.group(1).strip()
    street_raw = m.group(2).strip()

    # Normalize street suffix
    tokens = street_raw.split()
    if tokens:
        last = tokens[-1].lower().rstrip(".")
        if last in STREET_SUFFIX_NORMALIZE:
            tokens[-1] = STREET_SUFFIX_NORMALIZE[last]
    street_norm = " ".join(t.upper() for t in tokens)

    borough_code = ""
    bp = borough_part.lower().strip()
    for name, code in BOROUGH_NAMES.items():
        if name in bp:
            borough_code = code
            break

    normalized = f"{house_number} {street_norm}"
    log.info(
        "Parsed address: house=%s street=%s borough=%s",
        house_number,
        street_norm,
        borough_code or "?",
    )
    return {
        "raw": raw,
        "house_number": house_number,
        "street": street_norm,
        "borough": borough_code,
        "normalized": normalized,
    }


def lookup_bin_for_bbl(bbl: str) -> Optional[str]:
    """Find a BIN for a given BBL via Building Footprints.

    Returns the first non-placeholder BIN found. PLUTO BBLs come as
    decimals (e.g. '1012840033.00000000'); footprints stores them as
    integer strings, so we normalize.
    """
    if not bbl:
        return None
    bbl_norm = str(bbl).split(".")[0]
    for field in ("base_bbl", "mappluto_bbl"):
        params = {
            field: bbl_norm,
            "$limit": 5,
            "$select": "bin,base_bbl,mappluto_bbl",
        }
        try:
            resp = http_utils.get(BUILDING_FOOTPRINTS_ENDPOINT, params=params)
            rows = resp.json()
        except Exception as exc:
            log.warning("Footprints lookup failed (%s): %s", field, exc)
            continue
        for r in rows:
            bin_ = r.get("bin")
            if bin_ and str(bin_) not in ("1000000", "2000000", "3000000",
                                          "4000000", "5000000", "0"):
                log.info("BIN for BBL %s via %s: %s", bbl_norm, field, bin_)
                return str(bin_)
    log.warning("No BIN found for BBL %s", bbl)
    return None


def resolve_address(address: str) -> Optional[dict]:
    """Resolve address to BIN/BBL via PLUTO. Returns None if not found."""
    parsed = parse_address(address)

    # PLUTO address is "HOUSE STREET" format, all caps.
    target_addr = parsed["normalized"]
    where_clauses = [f"address='{target_addr}'"]
    if parsed["borough"]:
        where_clauses.append(f"borough='{parsed['borough']}'")

    params = {
        "$where": " AND ".join(where_clauses),
        "$limit": 5,
        "$select": (
            "bbl,address,borough,zipcode,block,lot,"
            "bldgarea,numfloors,yearbuilt,bldgclass,unitstotal,lotarea"
        ),
    }
    log.info("Querying PLUTO with: %s", params["$where"])
    try:
        resp = http_utils.get(PLUTO_ENDPOINT, params=params)
        rows = resp.json()
    except Exception as exc:
        log.error("PLUTO query failed: %s", exc)
        return None

    if not rows:
        # Fallback: fuzzy LIKE on street, exact on house number
        log.info("No exact match, trying fuzzy")
        like_clauses = [
            f"address like '{parsed['house_number']} %{parsed['street'].split()[-1]}%'"
        ]
        if parsed["borough"]:
            like_clauses.append(f"borough='{parsed['borough']}'")
        params = {
            "$where": " AND ".join(like_clauses),
            "$limit": 5,
            "$select": (
                "bbl,address,borough,zipcode,block,lot,"
                "bldgarea,numfloors,yearbuilt,bldgclass,unitstotal,lotarea"
            ),
        }
        try:
            resp = http_utils.get(PLUTO_ENDPOINT, params=params)
            rows = resp.json()
        except Exception as exc:
            log.error("PLUTO fuzzy query failed: %s", exc)
            return None

    if not rows:
        log.warning("No PLUTO match for %s", address)
        return None

    row = rows[0]
    bbl = row.get("bbl")
    bin_ = lookup_bin_for_bbl(bbl) if bbl else None

    def _num(v):
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    result = {
        "bin": bin_,
        "bbl": bbl,
        "borough": row.get("borough"),
        "block": row.get("block"),
        "lot": row.get("lot"),
        "zipcode": row.get("zipcode"),
        "normalized_address": row.get("address"),
        "house_number": parsed["house_number"],
        "street": parsed["street"],
        "raw_input": parsed["raw"],
        # PLUTO building metrics — used by takeoff_engine for real-sqft
        # scope estimation instead of the 1000 sqft placeholder.
        "bldg_area_sqft": _num(row.get("bldgarea")),
        "num_floors": _num(row.get("numfloors")),
        "year_built": int(_num(row.get("yearbuilt")) or 0) or None,
        "bldg_class": row.get("bldgclass"),
        "units_total": _num(row.get("unitstotal")),
        "lot_area_sqft": _num(row.get("lotarea")),
    }
    log.info("Resolved %s -> BIN=%s BBL=%s", address, result["bin"], result["bbl"])
    return result
