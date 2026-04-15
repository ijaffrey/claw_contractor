"""Thin wrapper around Anthropic SDK for Vision calls.

All Vision calls in this package go through here so the model ID, retry
policy, and request shape are consistent.
"""

import logging
import os
import time
from typing import Optional

import anthropic

log = logging.getLogger(__name__)

VISION_MODEL = "claude-opus-4-5"
DEFAULT_MAX_TOKENS = 1500
MAX_RETRIES = 3
BACKOFF = 3.0


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


def vision_message(
    image_b64: str,
    prompt: str,
    *,
    media_type: str = "image/jpeg",
    max_tokens: int = DEFAULT_MAX_TOKENS,
    system: Optional[str] = None,
) -> str:
    """Run a single-image Vision call and return the text response."""
    client = get_client()
    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            kwargs = {
                "model": VISION_MODEL,
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            }
            if system:
                kwargs["system"] = system
            resp = client.messages.create(**kwargs)
            parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
            return "".join(parts).strip()
        except anthropic.APIStatusError as exc:
            last_exc = exc
            log.warning(
                "Vision call failed (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF * attempt)
        except anthropic.APIError as exc:
            last_exc = exc
            log.warning(
                "Vision API error (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF * attempt)
    assert last_exc is not None
    raise last_exc
