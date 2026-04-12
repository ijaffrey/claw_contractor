"""Firm scraper — resolve contact info for a permit applicant firm.

Priority: Google search → LinkedIn → Apollo.io → Hunter.io → manual fallback.
Never crashes the pipeline — returns partial data with confidence: "low" on failure.
"""
from __future__ import annotations

import logging
import os
import re
import urllib.parse
from typing import Any

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_TIMEOUT = 3  # seconds per request
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

_EMPTY_FIRM: dict[str, Any] = {
    "firm_name": "",
    "logo_url": None,
    "address": None,
    "phone": None,
    "email": None,
    "website": None,
    "source": "not_found",
    "confidence": "low",
}

# Regex helpers
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}"
)


def scrape_firm(
    applicant_name: str, job_type: str = "contractor"
) -> dict[str, Any]:
    """Resolve contact info for *applicant_name*.

    Returns dict with keys: firm_name, logo_url, address, phone, email,
    website, source, confidence.
    """
    if not applicant_name or not applicant_name.strip():
        return {**_EMPTY_FIRM, "firm_name": "Unknown"}

    name = applicant_name.strip()
    result: dict[str, Any] = {**_EMPTY_FIRM, "firm_name": name}

    # 1. Google search → scrape first result
    try:
        info = _google_search(name, job_type)
        if info.get("website"):
            result.update(info)
            result["source"] = "website"
            result["confidence"] = "high" if info.get("email") else "medium"
            return result
    except Exception as exc:
        log.debug("Google scrape failed for %s: %s", name, exc)

    # 2. Apollo.io API
    apollo_key = os.environ.get("APOLLO_API_KEY")
    if apollo_key:
        try:
            info = _apollo_lookup(name, apollo_key)
            if info.get("email") or info.get("website"):
                result.update(info)
                result["source"] = "apollo"
                result["confidence"] = "high" if info.get("email") else "medium"
                return result
        except Exception as exc:
            log.debug("Apollo lookup failed for %s: %s", name, exc)

    # 3. Hunter.io API
    hunter_key = os.environ.get("HUNTER_API_KEY")
    if hunter_key:
        try:
            info = _hunter_lookup(name, hunter_key)
            if info.get("email"):
                result.update(info)
                result["source"] = "hunter"
                result["confidence"] = "medium"
                return result
        except Exception as exc:
            log.debug("Hunter lookup failed for %s: %s", name, exc)

    # 4. Manual fallback
    result["source"] = "not_found"
    result["confidence"] = "low"
    return result


# ---------------------------------------------------------------------------
# Google search + website scrape
# ---------------------------------------------------------------------------

def _google_search(name: str, job_type: str) -> dict[str, Any]:
    """Search Google for the firm and scrape first result."""
    role = "architect" if "architect" in job_type.lower() else "general contractor"
    query = f"{name} {role} NYC"
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=3"

    resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract first organic result URL
    first_url = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/url?q="):
            target = urllib.parse.unquote(href.split("/url?q=")[1].split("&")[0])
            if _is_valid_website(target):
                first_url = target
                break

    if not first_url:
        return {}

    return _scrape_website(first_url, name)


def _is_valid_website(url: str) -> bool:
    """Filter out Google, social, directory domains."""
    skip = ("google.", "youtube.", "facebook.", "twitter.", "yelp.", "bbb.",
            "linkedin.", "instagram.", "tiktok.", "mapquest.", "yellowpages.")
    lower = url.lower()
    return any(lower.startswith(p) for p in ("http://", "https://")) and not any(
        d in lower for d in skip
    )


def _scrape_website(url: str, firm_name: str) -> dict[str, Any]:
    """Scrape a firm website for contact info and logo."""
    result: dict[str, Any] = {"website": url}
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
    except Exception:
        return result

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Email
    emails = _EMAIL_RE.findall(text)
    # Also check mailto links
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("mailto:"):
            emails.append(a["href"].replace("mailto:", "").split("?")[0])
    # Filter out common non-contact emails
    filtered = [e for e in emails if not any(
        x in e.lower() for x in ("noreply", "no-reply", "example.", "sentry", "webpack")
    )]
    if filtered:
        result["email"] = filtered[0]

    # Phone
    phones = _PHONE_RE.findall(text)
    if phones:
        result["phone"] = phones[0]

    # Logo — look for img in header/nav with "logo" in class/alt/src
    for img in soup.find_all("img"):
        attrs = " ".join([
            img.get("class", [""])[0] if isinstance(img.get("class"), list) else str(img.get("class", "")),
            str(img.get("alt", "")),
            str(img.get("src", "")),
        ]).lower()
        if "logo" in attrs:
            src = img.get("src", "")
            if src:
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    from urllib.parse import urljoin
                    src = urljoin(url, src)
                result["logo_url"] = src
                break

    # Address — look for structured address or NYC address pattern
    addr_match = re.search(
        r"\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)"
        r"[,\s]+(?:Suite|Ste|Floor|Fl|#)?\s*\d*[,\s]*"
        r"(?:New York|NY|Manhattan|Brooklyn|Queens)",
        text,
        re.IGNORECASE,
    )
    if addr_match:
        result["address"] = addr_match.group(0).strip()

    return result


# ---------------------------------------------------------------------------
# Apollo.io API
# ---------------------------------------------------------------------------

def _apollo_lookup(name: str, api_key: str) -> dict[str, Any]:
    """Search Apollo.io for organization by name."""
    resp = requests.post(
        "https://api.apollo.io/v1/organizations/search",
        json={"q_organization_name": name, "page": 1, "per_page": 1},
        headers={"Content-Type": "application/json", "X-Api-Key": api_key},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    orgs = data.get("organizations", [])
    if not orgs:
        return {}
    org = orgs[0]
    return {
        "website": org.get("website_url"),
        "logo_url": org.get("logo_url"),
        "phone": org.get("phone"),
        "email": org.get("primary_email"),
        "address": org.get("raw_address"),
    }


# ---------------------------------------------------------------------------
# Hunter.io API
# ---------------------------------------------------------------------------

def _hunter_lookup(name: str, api_key: str) -> dict[str, Any]:
    """Search Hunter.io for domain + email by company name."""
    resp = requests.get(
        "https://api.hunter.io/v2/domain-search",
        params={"company": name, "api_key": api_key, "limit": 1},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    result: dict[str, Any] = {}
    if data.get("domain"):
        result["website"] = f"https://{data['domain']}"
    emails = data.get("emails", [])
    if emails:
        result["email"] = emails[0].get("value")
    return result
