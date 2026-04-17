"""Shared retry utilities for all scrapers.

Provides a decorator-based retry with configurable backoff, and a
rate-limit delay helper to avoid triggering upstream throttling.
"""

import time
import functools
import logging
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)


def with_retry(max_attempts=3, backoff_seconds=None, exceptions=(RequestException, Timeout, ConnectionError)):
    """Decorator: retry a function on transient network errors.

    Args:
        max_attempts: Total number of attempts (including the first).
        backoff_seconds: List of wait times between retries.
            Defaults to [5, 15, 30]. If fewer entries than retries,
            the last value is reused.
        exceptions: Tuple of exception classes to catch and retry on.

    Returns None (never crashes) if all attempts are exhausted.

    Usage::

        @with_retry(max_attempts=3, backoff_seconds=[5, 15, 30])
        def fetch_permit(permit_id):
            return requests.get(f"https://api.example.com/permits/{permit_id}")
    """
    if backoff_seconds is None:
        backoff_seconds = [5, 15, 30]

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_attempts - 1:
                        wait = backoff_seconds[min(attempt, len(backoff_seconds) - 1)]
                        logger.warning(
                            "%s failed (attempt %d/%d): %s. Retrying in %ds",
                            func.__name__, attempt + 1, max_attempts, e, wait,
                        )
                        time.sleep(wait)
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, max_attempts, e,
                        )
                        return None  # Never crash — return None on exhaustion
            return None
        return wrapper
    return decorator


def rate_limit_delay(seconds=2):
    """Sleep between requests to avoid triggering upstream rate limits.

    Call this between consecutive HTTP requests to the same host.

    Args:
        seconds: How long to sleep. Default 2s is conservative enough
            for most NYC/government APIs.
    """
    time.sleep(seconds)
