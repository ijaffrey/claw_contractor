"""pipeline_state.json — persistent state for address generation runs.

Schema:
{
  "schema_version": "1.0",
  "updated_at": "<iso8601>",
  "addresses": {
    "<address>": {
       "status": "queued"|"running"|"generated"|"error",
       "step": "<current step name>",
       "slug": "<slug>",
       "started_at": "<iso>",
       "updated_at": "<iso>",
       "error": "<optional>"
    }
  }
}
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = REPO_ROOT / "pipeline_state.json"
SCHEMA_VERSION = "1.0"
_LOCK = Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": _now_iso(),
        "addresses": {},
    }


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return _empty_state()
    try:
        with open(STATE_PATH) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return _empty_state()
    if "addresses" not in data:
        data["addresses"] = {}
    if "schema_version" not in data:
        data["schema_version"] = SCHEMA_VERSION
    return data


def save_state(state: dict[str, Any]) -> None:
    with _LOCK:
        state["updated_at"] = _now_iso()
        tmp = STATE_PATH.with_suffix(".json.tmp")
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, STATE_PATH)


def set_address_state(address: str, **fields: Any) -> dict[str, Any]:
    with _LOCK:
        state = load_state()
        entry = state["addresses"].get(address, {})
        if "started_at" not in entry:
            entry["started_at"] = _now_iso()
        entry.update(fields)
        entry["updated_at"] = _now_iso()
        state["addresses"][address] = entry
    save_state(state)
    return entry
