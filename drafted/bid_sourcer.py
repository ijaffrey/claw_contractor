"""Bid sourcer — create contractor notifications when an RFP is published.

Writes warm leads to contractor_notifications.json.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Lock
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTIFICATIONS_PATH = REPO_ROOT / "contractor_notifications.json"
MATCHES_PATH = REPO_ROOT / "rfp_matches.json"
ARCHITECT_RFPS_PATH = REPO_ROOT / "architect_rfps.json"

_LOCK = Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> list:
    if not path.exists():
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def _save_json(path: Path, data: list) -> None:
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)


def load_notifications() -> list[dict]:
    return _load_json(NOTIFICATIONS_PATH)


def save_notifications(notifications: list[dict]) -> None:
    _save_json(NOTIFICATIONS_PATH, notifications)


def source_bids(rfp_slug: str, trades: list[dict], architect_email: str = "") -> dict[str, Any]:
    """Create contractor notifications for a published RFP.

    Called when architect clicks Publish. Reads rfp_matches.json for
    matched contractors and writes warm leads to contractor_notifications.json.
    """
    with _LOCK:
        matches = _load_json(MATCHES_PATH)
        notifications = load_notifications()

        # Get RFP address and value
        rfps = _load_json(ARCHITECT_RFPS_PATH)
        rfp = next((r for r in rfps if r.get("slug") == rfp_slug), {})
        address = rfp.get("address") or rfp_slug.replace("_", " ").title()
        estimated_value = sum(t.get("total", 0) for t in trades)

        trade_names = [t.get("name", "") for t in trades]
        slug_matches = [m for m in matches if m.get("slug") == rfp_slug]

        # Remove any existing notifications for this slug (re-publish)
        notifications = [n for n in notifications if n.get("rfp_slug") != rfp_slug]

        queued = 0
        contractors_matched = set()
        for m in slug_matches:
            contractor = m.get("contractor_slug", "")
            if contractor in contractors_matched:
                continue
            contractors_matched.add(contractor)

            notification = {
                "notification_id": str(uuid.uuid4()),
                "rfp_slug": rfp_slug,
                "contractor_slug": contractor,
                "address": address,
                "trades": trade_names,
                "estimated_value": estimated_value,
                "rfp_published_at": _now(),
                "hook_email_scheduled_at": (
                    datetime.now(timezone.utc) + timedelta(hours=8)
                ).isoformat(),
                "hook_email_sent_at": None,
                "hook_email_status": "scheduled",
                "contractor_response": "pending",
                "architect_email": architect_email,
            }
            notifications.append(notification)
            queued += 1

            # Mark match as notified
            m["notified"] = True

        save_notifications(notifications)
        _save_json(MATCHES_PATH, matches)

    return {
        "contractors_matched": len(contractors_matched),
        "notifications_queued": queued,
    }


def get_pending_leads(contractor_slug: str = "") -> list[dict]:
    """Get pending warm leads for a contractor (or all if slug is empty)."""
    notifications = load_notifications()
    return [
        n for n in notifications
        if n.get("contractor_response") == "pending"
        and (not contractor_slug or n.get("contractor_slug") == contractor_slug)
    ]


def respond_to_lead(notification_id: str, response: str) -> dict | None:
    """Mark a lead as interested or not_interested."""
    with _LOCK:
        notifications = load_notifications()
        for n in notifications:
            if n.get("notification_id") == notification_id:
                n["contractor_response"] = response
                n["responded_at"] = _now()
                save_notifications(notifications)
                return n
    return None
