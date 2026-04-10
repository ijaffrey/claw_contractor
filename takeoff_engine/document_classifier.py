"""Classify PDF pages as FLOOR_PLAN / ELEVATION / SPEC_SHEET / FILING_FORM /
STRUCTURAL / MEP / OTHER using Claude Vision.
"""

import json
import logging
import re
from pathlib import Path
from typing import List

from . import pdf_utils, vision_client

log = logging.getLogger(__name__)

PAGE_TYPES = {
    "FLOOR_PLAN",
    "ELEVATION",
    "SPEC_SHEET",
    "FILING_FORM",
    "STRUCTURAL",
    "MEP",
    "OTHER",
}

CLASSIFY_PROMPT = """You are classifying a single page from a NYC DOB construction document.

Respond with exactly one JSON object and nothing else. Schema:
{
  "page_type": "FLOOR_PLAN" | "ELEVATION" | "SPEC_SHEET" | "FILING_FORM" | "STRUCTURAL" | "MEP" | "OTHER",
  "confidence": "high" | "medium" | "low",
  "short_description": "<one sentence>"
}

Guidance:
- FILING_FORM: NYC DOB PW1/PW2/TR1/other fillable application or permit forms
- FLOOR_PLAN: top-down architectural plan of a floor
- ELEVATION: exterior or interior elevation view
- SPEC_SHEET: written specifications, material callouts, schedules
- STRUCTURAL: framing, foundation, structural details
- MEP: mechanical/electrical/plumbing drawings
- OTHER: cover sheets, indices, unrelated content"""


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of a model response."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def classify_pdf(pdf_path: Path, *, dpi: int = 150, max_pages: int = 4) -> list:
    """Classify each page of a PDF. Returns list of page result dicts."""
    pdf_path = Path(pdf_path)
    images = pdf_utils.pdf_to_images(pdf_path, dpi=dpi, max_pages=max_pages)
    results: list = []
    for i, img in enumerate(images, start=1):
        b64 = pdf_utils.image_to_b64_jpeg(img)
        log.info(
            "Classifying %s page %d/%d via Vision", pdf_path.name, i, len(images)
        )
        try:
            text = vision_client.vision_message(b64, CLASSIFY_PROMPT)
        except Exception as exc:
            log.error(
                "Classify failed %s p.%d: %s", pdf_path.name, i, exc
            )
            results.append(
                {
                    "pdf": pdf_path.name,
                    "page": i,
                    "page_type": "OTHER",
                    "confidence": "low",
                    "short_description": f"classification_failed: {exc}",
                    "error": str(exc),
                }
            )
            continue
        parsed = _extract_json(text)
        page_type = parsed.get("page_type", "OTHER")
        if page_type not in PAGE_TYPES:
            page_type = "OTHER"
        results.append(
            {
                "pdf": pdf_path.name,
                "pdf_path": str(pdf_path),
                "page": i,
                "page_type": page_type,
                "confidence": parsed.get("confidence", "low"),
                "short_description": parsed.get("short_description", ""),
                "raw": text if not parsed else None,
            }
        )
    return results


def classify_all(pdf_paths: List[Path], *, max_pages: int = 4) -> list:
    """Classify a list of PDFs, flattening pages into one list."""
    out: list = []
    for p in pdf_paths:
        try:
            out.extend(classify_pdf(Path(p), max_pages=max_pages))
        except Exception as exc:
            log.error("classify_pdf crashed on %s: %s", p, exc)
    return out
