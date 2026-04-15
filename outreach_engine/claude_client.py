"""Anthropic SDK wrapper for outreach email generation.

Uses claude-sonnet-4-5 (Sonnet, not Opus) per Sprint C brief.
"""

import logging
import os
import time
from typing import Optional

import anthropic

log = logging.getLogger(__name__)

OUTREACH_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 1000
MAX_RETRIES = 3
BACKOFF = 2.5

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Source the patrick .env first."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def generate_text(
    prompt: str,
    *,
    system: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Single-turn text completion via Sonnet."""
    client = get_client()
    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            kwargs = {
                "model": OUTREACH_MODEL,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            resp = client.messages.create(**kwargs)
            parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
            return "".join(parts).strip()
        except anthropic.APIError as exc:
            last_exc = exc
            log.warning(
                "outreach LLM call failed (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF * attempt)
    assert last_exc is not None
    raise last_exc
