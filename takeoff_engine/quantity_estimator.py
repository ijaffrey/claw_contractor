"""Apply quantity rules + price sheet rates + markup to build line items."""

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Default quantity rules when floor area is known but specific quantities
# are not extractable from Vision. Fraction of floor_area used for each
# line item. Intentionally conservative — low confidence.
DEFAULT_AREA_FRACTIONS = {
    "abatement": {
        "floor_tile_removal": 0.80,
        "ceiling_tile": 0.70,
    },
    "concrete": {
        "slab_patching": 0.10,
    },
    "roofing": {
        "tpo_membrane": 1.0,  # roof area ~= footprint
    },
    "demo": {
        "interior_demo": 1.0,
        "debris_removal": 1.0,
    },
    "sitework": {
        "grading": 1.0,
    },
}

# Fallback floor area when nothing is known (a typical single floor).
FALLBACK_FLOOR_AREA_SQFT = 1000


def load_price_sheet(contractor: str, root: Path | None = None) -> dict:
    """Load a contractor's price sheet JSON."""
    root = root or Path(__file__).parent / "price_sheets"
    path = root / f"{contractor}.json"
    if not path.exists():
        raise FileNotFoundError(f"Price sheet not found: {path}")
    with open(path) as fh:
        return json.load(fh)


def _area_for_trade(shared: dict) -> tuple[float, str]:
    """Return (scope_area_sqft, confidence).

    Precedence:
      1. PLUTO typical floor plate (floor_area_source=pluto_*) — high
      2. Vision-extracted floor area (floor_area_source=vision_*) — medium
      3. FALLBACK_FLOOR_AREA_SQFT (1000) — low
    """
    fa = shared.get("floor_area_sqft_estimate")
    src = shared.get("floor_area_source")
    if isinstance(fa, (int, float)) and fa > 0:
        if src and src.startswith("pluto"):
            return float(fa), "high"
        return float(fa), "medium"
    return float(FALLBACK_FLOOR_AREA_SQFT), "low"


def build_line_items(
    trade: str,
    assessment: dict,
    shared: dict,
    price_sheet: dict,
) -> list:
    """Produce line items for an applicable trade."""
    if not assessment.get("applicable"):
        return []

    trade_rates: dict = (price_sheet.get("trades") or {}).get(trade) or {}
    if not trade_rates:
        log.warning("No rates for trade=%s in price sheet", trade)
        return []

    area_sqft, area_conf = _area_for_trade(shared)
    fractions = DEFAULT_AREA_FRACTIONS.get(trade, {})

    items: list = []
    for item_name, item_def in trade_rates.items():
        unit = item_def.get("unit", "sqft")
        rate = float(item_def.get("rate", 0.0))

        if unit == "sqft":
            frac = fractions.get(item_name, 0.0)
            qty = round(area_sqft * frac, 2) if frac else 0.0
            basis = f"{frac:.0%} of {area_sqft:.0f} sqft"
        elif unit == "lft":
            # Rough linear-feet heuristic: perimeter ~= 4 * sqrt(area)
            qty = round(4 * (area_sqft ** 0.5) * fractions.get(item_name, 0.0), 2)
            basis = f"perimeter heuristic from {area_sqft:.0f} sqft"
        elif unit == "each":
            qty = 0.0
            basis = "requires explicit count — none found"
        elif unit == "ton":
            qty = 0.0
            basis = "requires explicit tonnage — none found"
        elif unit == "cuyd":
            qty = 0.0
            basis = "requires excavation depth — none found"
        else:
            qty = 0.0
            basis = "unknown unit heuristic"

        subtotal = round(qty * rate, 2)
        item_conf = (
            "low" if qty == 0.0 or area_conf == "low" else assessment.get("confidence", "low")
        )
        items.append(
            {
                "trade": trade,
                "item": item_name,
                "unit": unit,
                "unit_rate": rate,
                "quantity": qty,
                "subtotal": subtotal,
                "basis": basis,
                "confidence": item_conf,
            }
        )
    return items


def apply_markup(subtotal: float, markup: dict) -> dict:
    oh = float(markup.get("overhead_pct", 0.0))
    pr = float(markup.get("profit_pct", 0.0))
    cn = float(markup.get("contingency_pct", 0.0))
    overhead = round(subtotal * oh, 2)
    profit = round(subtotal * pr, 2)
    contingency = round(subtotal * cn, 2)
    total = round(subtotal + overhead + profit + contingency, 2)
    return {
        "subtotal": round(subtotal, 2),
        "overhead": overhead,
        "profit": profit,
        "contingency": contingency,
        "overhead_pct": oh,
        "profit_pct": pr,
        "contingency_pct": cn,
        "total": total,
    }


def price_scope(
    scope: dict,
    price_sheet: dict,
    trades: list,
) -> dict[str, Any]:
    """Build priced line items for every requested trade.

    Returns dict with per-trade items, per-trade totals, and grand totals.
    """
    shared = scope.get("shared", {})
    trade_assessments = scope.get("trades", {})

    per_trade: dict = {}
    grand_subtotal = 0.0
    flags: list = []

    for trade in trades:
        assessment = trade_assessments.get(trade) or {
            "applicable": False,
            "trade": trade,
        }
        items = build_line_items(trade, assessment, shared, price_sheet)
        subtotal = sum(i["subtotal"] for i in items)
        trade_markup = apply_markup(
            subtotal, price_sheet.get("markup", {})
        )
        per_trade[trade] = {
            "applicable": assessment.get("applicable", False),
            "confidence": assessment.get("confidence", "low"),
            "reasons": assessment.get("reasons", []),
            "keywords_hit": assessment.get("keywords_hit", []),
            "line_items": items,
            "pricing": trade_markup,
        }
        grand_subtotal += subtotal
        for item in items:
            if item.get("confidence") == "low":
                flags.append(
                    f"low-confidence: {trade}.{item['item']} "
                    f"({item['basis']})"
                )
        if assessment.get("applicable") and not items:
            flags.append(
                f"trade {trade} marked applicable but no priceable line items"
            )

    grand_markup = apply_markup(grand_subtotal, price_sheet.get("markup", {}))

    return {
        "per_trade": per_trade,
        "grand_total": grand_markup,
        "flags": flags,
    }
