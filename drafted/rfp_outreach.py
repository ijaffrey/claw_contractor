"""RFP outreach — send hook email with pre-built RFP attached.

Queues to rfp_outreach_queue.json when Gmail is not configured.
"""
from __future__ import annotations

import json
import logging
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_PATH = REPO_ROOT / "rfp_outreach_queue.json"

DRAFTED_FROM_EMAIL = os.environ.get("DRAFTED_FROM_EMAIL", "sarah@drafted.com")
DRAFTED_FROM_NAME = os.environ.get("DRAFTED_FROM_NAME", "Sarah Chen")


def _contractor_count(bucket: str = "") -> int:
    """Vary contractor count between 2-4 based on bucket."""
    bucket_lower = (bucket or "").lower()
    if "gc" in bucket_lower or "general" in bucket_lower:
        return 3
    return random.choice([2, 3])


def compose_hook_email(
    address: str,
    firm_info: dict,
    rfp_path: str,
    bucket: str = "",
) -> dict[str, Any]:
    """Compose the hook email without sending it."""
    n = _contractor_count(bucket)
    to_email = firm_info.get("email") or ""
    firm_name = firm_info.get("firm_name") or "there"

    # Never mention DOB, permits, data sources, or AI
    body = (
        f"Hi,\n\n"
        f"Would you like GC and sub recommendations for {address}?\n\n"
        f"I have {n} contractors interested in the scope. I also put together a\n"
        f"draft RFP based on the project — free to use, edit, and send to\n"
        f"contractors directly.\n\n"
        f"[Draft RFP attached]\n\n"
        f"Let me know and I'll make the introductions.\n\n"
        f"{DRAFTED_FROM_NAME}\n"
        f"Project Coordinator, Drafted\n"
        f"{DRAFTED_FROM_EMAIL}"
    )

    return {
        "to": to_email,
        "from_email": DRAFTED_FROM_EMAIL,
        "from_name": DRAFTED_FROM_NAME,
        "subject": f"Contractors for {address}",
        "body": body,
        "attachment": rfp_path,
        "firm_name": firm_name,
    }


def send_rfp_hook(
    address_slug: str,
    firm_info: dict,
    rfp_path: str,
    bucket: str = "",
) -> dict[str, Any]:
    """Send the hook email or queue it.

    Returns ``{sent, email_used, timestamp, message_id, status}``.
    """
    address = address_slug.replace("_", " ").title()
    email_data = compose_hook_email(address, firm_info, rfp_path, bucket)

    to_email = email_data["to"]
    now = datetime.now(timezone.utc).isoformat()

    if not to_email:
        # No email — can't send
        _queue_email(address_slug, email_data, "no_email")
        return {
            "sent": False,
            "email_used": None,
            "timestamp": now,
            "message_id": None,
            "status": "no_email",
        }

    # Try Gmail OAuth if configured
    gmail_sent = _try_gmail_send(email_data)
    if gmail_sent:
        return {
            "sent": True,
            "email_used": to_email,
            "timestamp": now,
            "message_id": gmail_sent.get("id"),
            "status": "sent",
        }

    # Queue for manual send
    _queue_email(address_slug, email_data, "queued")
    return {
        "sent": False,
        "email_used": to_email,
        "timestamp": now,
        "message_id": None,
        "status": "queued",
    }


def _try_gmail_send(email_data: dict) -> dict | None:
    """Attempt to send via Gmail OAuth. Returns message dict or None."""
    # Reuse portal's Gmail infrastructure if available
    try:
        from portal.gmail_auth import get_gmail_service  # type: ignore
        service = get_gmail_service()
        if service is None:
            return None
    except (ImportError, Exception):
        return None

    # If we get here, Gmail is configured — build and send
    try:
        import base64
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication

        msg = MIMEMultipart()
        msg["to"] = email_data["to"]
        msg["from"] = f"{email_data['from_name']} <{email_data['from_email']}>"
        msg["subject"] = email_data["subject"]
        msg.attach(MIMEText(email_data["body"], "plain"))

        # Attach PDF
        pdf_path = Path(email_data.get("attachment", ""))
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                att = MIMEApplication(f.read(), _subtype="pdf")
                att.add_header("Content-Disposition", "attachment", filename=pdf_path.name)
                msg.attach(att)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        result = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return result
    except Exception as exc:
        log.error("Gmail send failed: %s", exc)
        return None


def _queue_email(slug: str, email_data: dict, status: str) -> None:
    """Append email to the outreach queue file."""
    queue = []
    if QUEUE_PATH.exists():
        try:
            with open(QUEUE_PATH) as f:
                queue = json.load(f)
        except (OSError, json.JSONDecodeError):
            queue = []

    queue.append({
        "slug": slug,
        "status": status,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        **email_data,
    })

    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2)
