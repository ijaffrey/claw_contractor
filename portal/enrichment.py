"""Filer enrichment — resolve filing-rep firm names to domains and contact emails."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parent.parent
OVERRIDES_PATH = Path(__file__).resolve().parent / "firm_domain_overrides.json"
CACHE_PATH = REPO_ROOT / "enrichment_cache.json"
CACHE_TTL_DAYS = 30

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HTTP_TIMEOUT = 8

AGGREGATOR_DOMAINS = {
    "linkedin.com", "yelp.com", "manta.com", "bbb.org", "dnb.com",
    "zoominfo.com", "buildzoom.com", "wikipedia.org", "indeed.com",
    "glassdoor.com", "facebook.com", "twitter.com", "x.com",
    "instagram.com", "youtube.com",
}

GENERIC_PREFIXES = {
    "info", "contact", "hello", "support", "admin", "sales",
    "office", "mail", "team", "help", "service", "services",
    "noreply", "no-reply",
}

BUSINESS_SUFFIXES = re.compile(
    r"\b(llc|inc|ltd|corp|co|pllc|pc|lp|associates|consultants|consulting)\b",
    re.IGNORECASE,
)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/team"]


@dataclass
class EnrichmentResult:
    firm_name: str
    normalized_key: str
    domain: Optional[str] = None
    domain_source: Optional[str] = None
    emails: list[str] = field(default_factory=list)
    pages_scraped: list[str] = field(default_factory=list)
    error: Optional[str] = None
    fetched_at: Optional[float] = None
    cached: bool = False


def normalize_firm_name(name: str) -> str:
    s = name.lower().strip()
    for ch in ".,;:'\"!@#&()":
        s = s.replace(ch, "")
    s = BUSINESS_SUFFIXES.sub("", s).strip()
    return " ".join(s.split())


def _load_overrides() -> dict[str, str]:
    if OVERRIDES_PATH.exists():
        with open(OVERRIDES_PATH) as f:
            return json.load(f)
    return {}


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    tmp = CACHE_PATH.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(cache, f, indent=2)
    os.replace(tmp, CACHE_PATH)


def _is_aggregator(url: str) -> bool:
    for agg in AGGREGATOR_DOMAINS:
        if agg in url:
            return True
    return False


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def find_firm_domain(firm_name: str) -> tuple[Optional[str], Optional[str]]:
    key = normalize_firm_name(firm_name)
    overrides = _load_overrides()
    if key in overrides:
        return overrides[key], "override"

    query = f"{firm_name} official website"
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    sess = _session()
    try:
        resp = sess.get(url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        return None, f"ddg_error: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")
    for link in soup.select("a.result__a"):
        href = link.get("href", "")
        if "uddg=" in href:
            qs = parse_qs(urlparse(href).query)
            href = qs.get("uddg", [href])[0]
        if not href.startswith("http"):
            continue
        if _is_aggregator(href):
            continue
        parsed = urlparse(href)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if domain:
            return domain, "ddg"

    return None, None


def scrape_firm_emails(domain: str) -> tuple[list[str], list[str]]:
    sess = _session()
    base_url = f"https://{domain}"
    emails_found: set[str] = set()
    pages_scraped: list[str] = []

    parts = domain.split(".")
    domain_root = parts[-2] if len(parts) >= 2 else domain

    paths_to_try = CONTACT_PATHS + ["/"]
    last_request_time = 0.0

    for path in paths_to_try:
        if path == "/" and emails_found:
            break

        url = urljoin(base_url, path)

        elapsed = time.time() - last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)

        try:
            last_request_time = time.time()
            resp = sess.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
            if resp.status_code >= 400:
                continue
            pages_scraped.append(path)
            page_emails = set(EMAIL_RE.findall(resp.text))
            for e in page_emails:
                e_lower = e.lower()
                local_part = e_lower.split("@")[0]
                e_domain = e_lower.split("@")[1]
                if domain_root not in e_domain:
                    continue
                if local_part in GENERIC_PREFIXES:
                    continue
                emails_found.add(e_lower)
        except Exception:
            continue

    return sorted(emails_found), pages_scraped


def enrich_firm(firm_name: str, force_refresh: bool = False) -> EnrichmentResult:
    key = normalize_firm_name(firm_name)
    now = time.time()

    if not force_refresh:
        cache = _load_cache()
        if key in cache:
            entry = cache[key]
            fetched_at = entry.get("fetched_at")
            if isinstance(fetched_at, (int, float)):
                age_days = (now - fetched_at) / 86400
                if age_days < CACHE_TTL_DAYS:
                    return EnrichmentResult(
                        firm_name=entry.get("firm_name", firm_name),
                        normalized_key=key,
                        domain=entry.get("domain"),
                        domain_source=entry.get("domain_source"),
                        emails=entry.get("emails", []),
                        pages_scraped=entry.get("pages_scraped", []),
                        error=entry.get("error"),
                        fetched_at=fetched_at,
                        cached=True,
                    )

    domain, domain_source = find_firm_domain(firm_name)
    result = EnrichmentResult(
        firm_name=firm_name,
        normalized_key=key,
        domain=domain,
        domain_source=domain_source,
        fetched_at=now,
    )

    if not domain:
        result.error = "could not resolve domain"
    else:
        emails, pages = scrape_firm_emails(domain)
        result.emails = emails
        result.pages_scraped = pages

    cache = _load_cache()
    cache[key] = asdict(result)
    cache[key].pop("cached", None)
    _save_cache(cache)

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m portal.enrichment 'FIRM NAME'")
        sys.exit(1)
    name = " ".join(sys.argv[1:])
    result = enrich_firm(name, force_refresh=True)
    print(json.dumps(asdict(result), indent=2))
