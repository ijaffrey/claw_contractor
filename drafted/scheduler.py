"""APScheduler jobs — contractor hook emails + architect morning summaries.

Queues to email_queue.json when Gmail is not configured.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
EMAIL_QUEUE_PATH = REPO_ROOT / "email_queue.json"
PORTAL_BASE = "http://100.84.10.48:5000"


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


def _queue_email(to: str, subject: str, body: str) -> None:
    """Append an email to the queue for manual review."""
    queue = _load_json(EMAIL_QUEUE_PATH)
    queue.append({
        "to": to,
        "subject": subject,
        "body": body,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "sent": False,
    })
    _save_json(EMAIL_QUEUE_PATH, queue)


def _try_send_email(to: str, subject: str, body: str) -> bool:
    """Try Gmail OAuth, fall back to queue."""
    try:
        from portal.gmail_auth import get_gmail_service
        service = get_gmail_service()
        if service:
            import base64
            from email.mime.text import MIMEText
            msg = MIMEText(body, "plain")
            msg["to"] = to
            msg["from"] = "sarah@drafted.com"
            msg["subject"] = subject
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            service.users().messages().send(userId="me", body={"raw": raw}).execute()
            return True
    except Exception:
        pass
    _queue_email(to, subject, body)
    return False


# ---------------------------------------------------------------------------
# Job 1: Contractor hook emails (hourly)
# ---------------------------------------------------------------------------

def send_contractor_hooks() -> None:
    """Check for due contractor notifications and send hook emails."""
    from drafted.bid_sourcer import load_notifications, save_notifications

    now = datetime.now(timezone.utc)
    notifications = load_notifications()
    sent_count = 0

    for n in notifications:
        if n.get("hook_email_status") != "scheduled":
            continue
        scheduled = n.get("hook_email_scheduled_at", "")
        if not scheduled:
            continue
        try:
            sched_dt = datetime.fromisoformat(scheduled)
        except (ValueError, TypeError):
            continue
        if sched_dt > now:
            continue

        # Due — compose and send
        address = n.get("address", "Unknown")
        trades = n.get("trades", [])
        value = n.get("estimated_value", 0)
        slug = n.get("rfp_slug", "")

        subject = f"New project match — {address}"
        body = (
            f"Hi Nauman,\n\n"
            f"A new project has been published on Drafted that matches your trade profile.\n\n"
            f"Project: {address}\n"
            f"Trades: {', '.join(trades)}\n"
            f"Estimated value: ${value:,.0f}\n\n"
            f"The architect is accepting bids. Would you like to submit a proposal?\n\n"
            f"View project: {PORTAL_BASE}/proposal/{slug}\n\n"
            f"Sarah Chen\n"
            f"Drafted"
        )

        to = "nauman@sanz.com"  # Placeholder — will be looked up from contractor profile
        sent = _try_send_email(to, subject, body)
        n["hook_email_status"] = "sent" if sent else "queued"
        n["hook_email_sent_at"] = datetime.now(timezone.utc).isoformat()
        sent_count += 1

    if sent_count:
        save_notifications(notifications)
        log.info("Sent %d contractor hook emails", sent_count)


# ---------------------------------------------------------------------------
# Job 2: Architect morning summary (daily at 7am)
# ---------------------------------------------------------------------------

def send_architect_summaries() -> None:
    """Send morning summary to each architect with published RFPs."""
    rfps_path = REPO_ROOT / "architect_rfps.json"
    rfps = _load_json(rfps_path)
    notifications = _load_json(REPO_ROOT / "contractor_notifications.json")

    # Group by architect
    by_architect: dict[str, list] = {}
    for r in rfps:
        if r.get("status") not in ("published", "bids_received"):
            continue
        owner = r.get("owner", "")
        if owner:
            by_architect.setdefault(owner, []).append(r)

    for email, arch_rfps in by_architect.items():
        lines = ["Hi,\n", "Here's where your bids stand.\n"]
        for r in arch_rfps:
            slug = r.get("slug", "")
            address = r.get("address", slug)
            notified = sum(1 for n in notifications if n.get("rfp_slug") == slug)
            interested = sum(
                1 for n in notifications
                if n.get("rfp_slug") == slug and n.get("contractor_response") == "interested"
            )
            published = (r.get("published_at") or r.get("created_at") or "")[:10]

            lines.append(f"--- {address} ---")
            lines.append(f"Contractors notified: {notified}")
            lines.append(f"Proposals received: {interested}")
            lines.append(f"RFP published: {published}")
            lines.append(f"View: {PORTAL_BASE}/architect/rfp/{slug}\n")

        lines.append("Drafted")
        body = "\n".join(lines)
        subject = f"Your RFPs — bid update ({len(arch_rfps)} project{'s' if len(arch_rfps) != 1 else ''})"
        _try_send_email(email, subject, body)

    log.info("Sent morning summaries to %d architects", len(by_architect))


def load_email_queue() -> list[dict]:
    return _load_json(EMAIL_QUEUE_PATH)
