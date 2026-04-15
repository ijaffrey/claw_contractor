"""Load a contractor profile JSON (from /contractors/<slug>.json)."""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

PROFILE_ROOT = Path(__file__).resolve().parent.parent / "contractors"


def load_profile(slug: str) -> dict:
    """Load /contractors/<slug>.json and return as dict."""
    path = PROFILE_ROOT / f"{slug}.json"
    if not path.exists():
        raise FileNotFoundError(f"Contractor profile not found: {path}")
    with open(path) as fh:
        return json.load(fh)
