"""RFP state tracking — extends pipeline_state.json with RFP fields."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = REPO_ROOT / "pipeline_state.json"
_LOCK = Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"schema_version": "1.0", "addresses": {}}
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"schema_version": "1.0", "addresses": {}}


def _save(state: dict[str, Any]) -> None:
    state["updated_at"] = _now()
    tmp = STATE_PATH.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    tmp.replace(STATE_PATH)


def _slugify(address: str) -> str:
    s = (address or "").lower().strip()
    for ch in [",", ".", "'", '"']:
        s = s.replace(ch, "")
    return "_".join(s.split())


def get_rfp_state(slug: str) -> dict[str, Any]:
    """Get RFP-related fields for an address slug."""
    with _LOCK:
        state = _load()
        for addr, entry in state.get("addresses", {}).items():
            if _slugify(addr) == slug or entry.get("slug") == slug:
                return {
                    "firm_name": entry.get("firm_name"),
                    "firm_email": entry.get("firm_email"),
                    "firm_logo_url": entry.get("firm_logo_url"),
                    "firm_scrape_source": entry.get("firm_scrape_source"),
                    "rfp_built_at": entry.get("rfp_built_at"),
                    "rfp_pdf_path": entry.get("rfp_pdf_path"),
                    "rfp_html_path": entry.get("rfp_html_path"),
                    "rfp_hook_sent_at": entry.get("rfp_hook_sent_at"),
                    "rfp_hook_status": entry.get("rfp_hook_status"),
                    "rfp_response_status": entry.get("rfp_response_status"),
                    "rfp_response_at": entry.get("rfp_response_at"),
                }
    return {}


def update_rfp_state(slug: str, **fields: Any) -> dict[str, Any]:
    """Update RFP fields for an address slug. Creates entry if not found."""
    with _LOCK:
        state = _load()
        target_addr = None
        for addr, entry in state.get("addresses", {}).items():
            if _slugify(addr) == slug or entry.get("slug") == slug:
                target_addr = addr
                break

        if target_addr is None:
            target_addr = slug.replace("_", " ").title()
            state.setdefault("addresses", {})[target_addr] = {"slug": slug}

        entry = state["addresses"][target_addr]
        entry.update(fields)
        entry["updated_at"] = _now()
        _save(state)
        return entry
