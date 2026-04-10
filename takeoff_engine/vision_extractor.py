"""Run trade-specific Claude Vision extraction on classified PDF pages."""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from . import pdf_utils, vision_client

log = logging.getLogger(__name__)

FILING_FORM_PROMPT = """You are extracting structured data from a NYC DOB PW1 / PW2 / TR1 filing form image.

Return exactly one JSON object, no other text. Schema:
{
  "description_of_work": "<string or null>",
  "estimated_cost_usd": <number or null>,
  "job_type": "<string or null>",
  "occupancy": "<string or null>",
  "building_year": <number or null>,
  "floor_area_sqft": <number or null>,
  "floors_affected": "<string or null>",
  "materials_mentioned": ["<string>", ...],
  "hazardous_material_notes": "<string or null>",
  "is_blank_template": <true|false>,
  "confidence": "high" | "medium" | "low"
}

If a field is not visible or unknowable, use null. If the form is blank/unfilled
(template only), set is_blank_template=true and confidence=low."""

FLOOR_PLAN_PROMPT = """You are extracting scope data from a NYC construction floor plan.

Return exactly one JSON object, no other text. Schema:
{
  "floor_area_sqft": <number or null>,
  "room_types": ["<string>", ...],
  "demo_notes": "<string or null>",
  "new_construction_notes": "<string or null>",
  "material_callouts": ["<string>", ...],
  "hazardous_material_notes": "<string or null>",
  "confidence": "high" | "medium" | "low"
}

Use null for unknown fields."""

SPEC_SHEET_PROMPT = """You are extracting a material + trade scope from a construction spec sheet.

Return exactly one JSON object, no other text. Schema:
{
  "materials": [
    { "name": "<string>", "quantity": <number or null>, "unit": "<string or null>" }
  ],
  "trades_described": ["<string>", ...],
  "total_sqft": <number or null>,
  "hazardous_material_references": ["<string>", ...],
  "confidence": "high" | "medium" | "low"
}

Use null for unknown. Omit empty arrays."""

PROMPT_BY_PAGE_TYPE = {
    "FILING_FORM": FILING_FORM_PROMPT,
    "FLOOR_PLAN": FLOOR_PLAN_PROMPT,
    "SPEC_SHEET": SPEC_SHEET_PROMPT,
    # Structural/MEP/Elevation fall back to FLOOR_PLAN-style extraction
    "STRUCTURAL": FLOOR_PLAN_PROMPT,
    "MEP": FLOOR_PLAN_PROMPT,
    "ELEVATION": FLOOR_PLAN_PROMPT,
}


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def _dpi_for_type(page_type: str) -> int:
    return 200 if page_type == "SPEC_SHEET" else 150


def extract_from_page(page_record: dict) -> Optional[dict]:
    """Run the right Vision prompt for a classified page and return data."""
    page_type = page_record.get("page_type", "OTHER")
    if page_type == "OTHER":
        log.info(
            "Skipping extraction for %s p.%d (type=OTHER)",
            page_record.get("pdf"),
            page_record.get("page"),
        )
        return None

    prompt = PROMPT_BY_PAGE_TYPE.get(page_type)
    if not prompt:
        return None

    pdf_path = Path(page_record["pdf_path"])
    page = page_record["page"]
    dpi = _dpi_for_type(page_type)
    images = pdf_utils.pdf_to_images(
        pdf_path, dpi=dpi, max_pages=page
    )
    if len(images) < page:
        log.warning(
            "Could not render %s page %d (only %d rendered)",
            pdf_path.name,
            page,
            len(images),
        )
        return None
    img = images[page - 1]
    b64 = pdf_utils.image_to_b64_jpeg(img)

    log.info(
        "Extracting %s p.%d (type=%s) via Vision", pdf_path.name, page, page_type
    )
    try:
        text = vision_client.vision_message(b64, prompt, max_tokens=1500)
    except Exception as exc:
        log.error("Extract failed %s p.%d: %s", pdf_path.name, page, exc)
        return {
            "page_type": page_type,
            "error": str(exc),
            "pdf": pdf_path.name,
            "page": page,
        }

    data = _extract_json(text)
    data["page_type"] = page_type
    data["pdf"] = pdf_path.name
    data["page"] = page
    if not data or (len(data) <= 3 and "error" not in data):
        data["raw"] = text
    return data


def extract_all(classified_pages: list) -> list:
    """Run extraction on every non-OTHER classified page."""
    out: list = []
    for p in classified_pages:
        try:
            r = extract_from_page(p)
            if r is not None:
                out.append(r)
        except Exception as exc:
            log.error("extract_from_page crashed: %s", exc)
    return out
