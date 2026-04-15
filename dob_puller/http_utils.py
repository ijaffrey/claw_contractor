"""Shared HTTP utilities: retry on 503, logging, bounded timeouts."""

import logging
import time
from typing import Optional

import requests

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 2.0
RETRY_STATUSES = {500, 502, 503, 504}
# 403/404/401 are terminal — no point retrying
NO_RETRY_STATUSES = {400, 401, 403, 404}


def get(
    url: str,
    *,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
) -> requests.Response:
    """GET with retry on transient errors. Raises on final failure."""
    sess = session or requests
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            resp = sess.get(url, params=params, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            last_exc = exc
            log.warning(
                "GET %s failed: %s (attempt %d/%d)", url, exc, attempt, retries
            )
            if attempt < retries:
                time.sleep(backoff * attempt)
            continue
        if resp.status_code in NO_RETRY_STATUSES:
            log.info("GET %s -> %s (no retry)", url, resp.status_code)
            resp.raise_for_status()  # terminal
            return resp
        if resp.status_code in RETRY_STATUSES:
            log.warning(
                "GET %s returned %s (attempt %d/%d)",
                url,
                resp.status_code,
                attempt,
                retries,
            )
            last_exc = requests.HTTPError(f"{resp.status_code} on {url}")
            if attempt < retries:
                time.sleep(backoff * attempt)
            continue
        resp.raise_for_status()
        return resp
    assert last_exc is not None
    raise last_exc


def post(
    url: str,
    *,
    data: Optional[dict] = None,
    json: Optional[dict] = None,
    headers: Optional[dict] = None,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
) -> requests.Response:
    """POST with retry on transient errors."""
    sess = session or requests
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            resp = sess.post(
                url, data=data, json=json, headers=headers, timeout=timeout
            )
            if resp.status_code in RETRY_STATUSES:
                log.warning(
                    "POST %s returned %s (attempt %d/%d)",
                    url,
                    resp.status_code,
                    attempt,
                    retries,
                )
                if attempt < retries:
                    time.sleep(backoff * attempt)
                    continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            log.warning(
                "POST %s failed: %s (attempt %d/%d)", url, exc, attempt, retries
            )
            if attempt < retries:
                time.sleep(backoff * attempt)
    assert last_exc is not None
    raise last_exc
