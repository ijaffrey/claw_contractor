"""PDF → image conversion and base64 encoding for Vision API."""

import base64
import io
import logging
from pathlib import Path
from typing import List

from pdf2image import convert_from_path
from PIL import Image

log = logging.getLogger(__name__)

DEFAULT_DPI_PLANS = 150
DEFAULT_DPI_SPECS = 200
MAX_PAGES_PER_PDF = 10  # keep Vision budget bounded
MAX_IMAGE_BYTES = 4_500_000  # stay under Anthropic 5 MB image limit


def pdf_to_images(
    pdf_path: Path,
    *,
    dpi: int = DEFAULT_DPI_PLANS,
    max_pages: int = MAX_PAGES_PER_PDF,
) -> List[Image.Image]:
    """Render a PDF to PIL images, capped at max_pages."""
    pdf_path = Path(pdf_path)
    log.info("Rendering %s at %d DPI (max %d pages)", pdf_path.name, dpi, max_pages)
    try:
        images = convert_from_path(
            str(pdf_path), dpi=dpi, first_page=1, last_page=max_pages
        )
    except Exception as exc:
        log.error("pdf2image failed for %s: %s", pdf_path, exc)
        return []
    log.info("Rendered %d page(s) from %s", len(images), pdf_path.name)
    return images


def image_to_b64_jpeg(
    img: Image.Image, *, quality: int = 80, max_side: int = 2000
) -> str:
    """Downscale + JPEG-encode a PIL image to a base64 string.

    Downsizes to stay safely under Anthropic's 5 MB image limit.
    """
    w, h = img.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    data = buf.getvalue()
    # If still too large, drop quality
    q = quality
    while len(data) > MAX_IMAGE_BYTES and q > 30:
        q -= 15
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q, optimize=True)
        data = buf.getvalue()
    log.debug("Encoded image: %d bytes (q=%d)", len(data), q)
    return base64.standard_b64encode(data).decode("ascii")
