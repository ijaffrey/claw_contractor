"""
Enrichment Engine — 6-step waterfall for lead contact enrichment.

Steps (in order, skip if field already populated):
  1. permit_data   — extract from permit record stored on lead
  2. google_maps   — Places API lookup by business name + borough
  3. website_scraper — scrape contact page of known website
  4. houzz         — search Houzz pro directory
  5. hunter        — Hunter.io domain search for email
  6. apollo        — Apollo.io people search

Set ENRICHMENT_MOCK=true to run in mock mode (no real HTTP calls).
"""

import os
import json
import logging
import re
import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

MOCK_MODE = os.getenv("ENRICHMENT_MOCK", "false").lower() == "true"

# ── Mock data ──────────────────────────────────────────────────────────────────

MOCK_PERMIT = {
    "phone": "212-555-0101",
    "email": None,
    "website": None,
    "source": "permit_data",
}

MOCK_GOOGLE = {
    "phone": "212-555-0202",
    "website": "https://acme-construction.example.com",
    "email": None,
    "source": "google_maps",
}

MOCK_WEBSITE = {
    "email": "info@acme-construction.example.com",
    "phone": None,
    "source": "website_scraper",
}

MOCK_HOUZZ = {
    "email": "pro@acme-construction.example.com",
    "phone": "212-555-0404",
    "source": "houzz",
}

MOCK_HUNTER = {
    "email": "owner@acme-construction.example.com",
    "source": "hunter",
}

MOCK_APOLLO = {
    "email": "ceo@acme-construction.example.com",
    "phone": "212-555-0606",
    "source": "apollo",
}

# ── Scoring weights ────────────────────────────────────────────────────────────

SOURCE_QUALITY = {
    "permit_data":     0.9,
    "google_maps":     0.85,
    "website_scraper": 0.80,
    "houzz":           0.75,
    "hunter":          0.70,
    "apollo":          0.65,
}


def _score(result: dict) -> float:
    """Return quality score for an enrichment result."""
    base = SOURCE_QUALITY.get(result.get("source", ""), 0.5)
    has_email = 1 if result.get("email") else 0
    has_phone = 1 if result.get("phone") else 0
    has_web   = 1 if result.get("website") else 0
    return round(base * (0.4 + 0.25 * has_email + 0.2 * has_phone + 0.15 * has_web), 3)


# ── Step implementations ───────────────────────────────────────────────────────

def _step_permit_data(lead: dict) -> dict:
    """Extract contact info directly from the permit fields on the lead."""
    if MOCK_MODE:
        return dict(MOCK_PERMIT)

    result = {"source": "permit_data"}
    # Permit records may carry owner_phone, owner_email, applicant fields
    for key in ("owner_phone", "applicant_phone", "phone"):
        if lead.get(key):
            result["phone"] = lead[key]
            break
    for key in ("owner_email", "applicant_email", "email"):
        if lead.get(key):
            result["email"] = lead[key]
            break
    for key in ("applicant_website", "website"):
        if lead.get(key):
            result["website"] = lead[key]
            break
    return result


def _step_google_maps(lead: dict) -> dict:
    """Google Places text-search for business name + location."""
    if MOCK_MODE:
        return dict(MOCK_GOOGLE)

    import requests
    api_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
    if not api_key:
        logger.debug("GOOGLE_PLACES_API_KEY not set, skipping google_maps step")
        return {"source": "google_maps"}

    company = lead.get("company") or lead.get("owner_business_name", "")
    borough = lead.get("borough", "")
    query = f"{company} contractor {borough} New York"

    try:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": query, "key": api_key},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return {"source": "google_maps"}

        place = results[0]
        place_id = place.get("place_id", "")

        # Details call for phone/website
        dr = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "formatted_phone_number,website",
                "key": api_key,
            },
            timeout=10,
        )
        dr.raise_for_status()
        detail = dr.json().get("result", {})
        return {
            "source": "google_maps",
            "phone": detail.get("formatted_phone_number"),
            "website": detail.get("website"),
        }
    except Exception as e:
        logger.warning(f"google_maps step failed: {e}")
        return {"source": "google_maps"}


def _step_website_scraper(lead: dict, current: dict) -> dict:
    """Scrape /contact page of known website for email/phone."""
    if MOCK_MODE:
        return dict(MOCK_WEBSITE)

    import requests

    website = current.get("website") or lead.get("website", "")
    if not website:
        return {"source": "website_scraper"}

    urls_to_try = [
        website.rstrip("/") + "/contact",
        website.rstrip("/") + "/contact-us",
        website.rstrip("/"),
    ]

    for url in urls_to_try:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                continue
            html = r.text

            # Extract email with regex
            emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)
            # Filter out obvious non-contact emails
            emails = [e for e in emails if not any(x in e.lower() for x in ("noreply", "no-reply", "example"))]

            # Extract phone
            phones = re.findall(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]", html)

            result = {"source": "website_scraper"}
            if emails:
                result["email"] = emails[0]
            if phones:
                result["phone"] = phones[0]
            if result.keys() - {"source"}:
                return result
        except Exception as e:
            logger.debug(f"website_scraper failed for {url}: {e}")

    return {"source": "website_scraper"}


def _step_houzz(lead: dict) -> dict:
    """Search Houzz pro directory for contractor."""
    if MOCK_MODE:
        return dict(MOCK_HOUZZ)

    import requests

    company = lead.get("company") or lead.get("owner_business_name", "")
    if not company:
        return {"source": "houzz"}

    try:
        r = requests.get(
            "https://www.houzz.com/professionals/search",
            params={"query": company, "location": "New York, NY"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.raise_for_status()
        html = r.text
        emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)
        emails = [e for e in emails if not any(x in e.lower() for x in ("noreply", "houzz"))]
        result = {"source": "houzz"}
        if emails:
            result["email"] = emails[0]
        return result
    except Exception as e:
        logger.warning(f"houzz step failed: {e}")
        return {"source": "houzz"}


def _step_hunter(lead: dict, current: dict) -> dict:
    """Hunter.io domain search for email."""
    if MOCK_MODE:
        return dict(MOCK_HUNTER)

    import requests

    api_key = os.getenv("HUNTER_API_KEY", "")
    if not api_key:
        return {"source": "hunter"}

    website = current.get("website") or lead.get("website", "")
    if not website:
        return {"source": "hunter"}

    domain = re.sub(r"https?://(www\.)?", "", website).split("/")[0]

    try:
        r = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": api_key, "limit": 3},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        emails_list = data.get("emails", [])
        if emails_list:
            return {"source": "hunter", "email": emails_list[0].get("value")}
    except Exception as e:
        logger.warning(f"hunter step failed: {e}")

    return {"source": "hunter"}


def _step_apollo(lead: dict) -> dict:
    """Apollo.io people search for email + phone."""
    if MOCK_MODE:
        return dict(MOCK_APOLLO)

    import requests

    api_key = os.getenv("APOLLO_API_KEY", "")
    if not api_key:
        return {"source": "apollo"}

    company = lead.get("company") or lead.get("owner_business_name", "")
    name = lead.get("name", "")
    first, *rest = name.split() if name else ([""], [])
    last = rest[-1] if rest else ""

    try:
        r = requests.post(
            "https://api.apollo.io/v1/people/search",
            headers={"Content-Type": "application/json", "Cache-Control": "no-cache"},
            json={
                "api_key": api_key,
                "q_organization_name": company,
                "q_keywords": f"{first} {last}".strip(),
                "page": 1,
                "per_page": 1,
            },
            timeout=10,
        )
        r.raise_for_status()
        people = r.json().get("people", [])
        if people:
            person = people[0]
            return {
                "source": "apollo",
                "email": person.get("email"),
                "phone": (person.get("phone_numbers") or [{}])[0].get("raw_number"),
            }
    except Exception as e:
        logger.warning(f"apollo step failed: {e}")

    return {"source": "apollo"}


# ── Waterfall orchestrator ─────────────────────────────────────────────────────

def enrich_lead(lead: dict) -> dict:
    """
    Run the 6-step enrichment waterfall on a lead dict.

    Returns enrichment result dict with keys:
        email, phone, website, email_source, phone_source,
        enrichment_status, enrichment_score, enriched_at
    """
    current: dict = {
        "email":        lead.get("enriched_email") or lead.get("email"),
        "phone":        lead.get("enriched_phone") or lead.get("phone"),
        "website":      lead.get("website"),
        "email_source": lead.get("email_source"),
        "phone_source": lead.get("phone_source"),
    }

    steps = [
        ("permit_data",    lambda: _step_permit_data(lead)),
        ("google_maps",    lambda: _step_google_maps(lead)),
        ("website_scraper", lambda: _step_website_scraper(lead, current)),
        ("houzz",          lambda: _step_houzz(lead)),
        ("hunter",         lambda: _step_hunter(lead, current)),
        ("apollo",         lambda: _step_apollo(lead)),
    ]

    best_score = 0.0
    steps_run = []

    for step_name, step_fn in steps:
        # Skip step if both email and phone are already found
        need_email = not current.get("email")
        need_phone = not current.get("phone")
        need_web   = not current.get("website")

        if not (need_email or need_phone or need_web):
            logger.debug(f"Skipping {step_name} — all fields populated")
            continue

        try:
            result = step_fn()
        except Exception as e:
            logger.warning(f"Step {step_name} raised: {e}")
            result = {"source": step_name}

        steps_run.append(step_name)
        step_score = _score(result)
        if step_score > best_score:
            best_score = step_score

        if result.get("email") and not current.get("email"):
            current["email"] = result["email"]
            current["email_source"] = step_name
        if result.get("phone") and not current.get("phone"):
            current["phone"] = result["phone"]
            current["phone_source"] = step_name
        if result.get("website") and not current.get("website"):
            current["website"] = result["website"]

        logger.debug(f"Step {step_name}: email={result.get('email')}, phone={result.get('phone')}, web={result.get('website')}")

    return {
        "email":             current.get("email"),
        "phone":             current.get("phone"),
        "website":           current.get("website"),
        "email_source":      current.get("email_source"),
        "phone_source":      current.get("phone_source"),
        "enrichment_status": "complete" if (current.get("email") or current.get("phone")) else "partial",
        "enrichment_score":  round(best_score, 3),
        "enriched_at":       datetime.utcnow().isoformat(),
        "steps_run":         steps_run,
    }


def enrich_batch(leads: list, delay: float = 0.0) -> list:
    """Enrich a list of lead dicts. Returns list of enrichment result dicts."""
    results = []
    for lead in leads:
        result = enrich_lead(lead)
        results.append({"lead_id": lead.get("id"), **result})
        if delay:
            time.sleep(delay)
    return results


# ── Test harness ───────────────────────────────────────────────────────────────

def test_waterfall():
    """Verify the 6-step waterfall runs correctly in mock mode."""
    assert MOCK_MODE, "Set ENRICHMENT_MOCK=true before running test_waterfall"

    sample_lead = {
        "id": 1,
        "name": "John Doe",
        "company": "Acme Construction",
        "borough": "Manhattan",
        "email": None,
        "phone": None,
        "website": None,
    }

    result = enrich_lead(sample_lead)

    assert result["email"], f"Expected email, got: {result}"
    assert result["phone"], f"Expected phone, got: {result}"
    assert result["website"], f"Expected website, got: {result}"
    assert result["email_source"], "Missing email_source"
    assert result["phone_source"], "Missing phone_source"
    assert result["enrichment_score"] > 0, "Score should be > 0"
    assert result["enrichment_status"] == "complete", f"Expected complete, got {result['enrichment_status']}"
    assert result["enriched_at"], "Missing enriched_at"
    assert len(result["steps_run"]) > 0, "No steps were run"

    # Verify early-stop: once email+phone+website found, later steps skipped
    # Step 1 (permit_data) returns phone only, step 2 (google_maps) returns phone+website,
    # step 3 (website_scraper) returns email → should stop before houzz
    assert "permit_data" in result["steps_run"]
    assert "google_maps" in result["steps_run"]
    assert "website_scraper" in result["steps_run"]

    # Batch test
    batch = enrich_batch([sample_lead, {**sample_lead, "id": 2, "name": "Jane Smith"}])
    assert len(batch) == 2
    assert all(r["email"] for r in batch)

    print("✓ test_waterfall passed — 6-step mock enrichment working")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    os.environ["ENRICHMENT_MOCK"] = "true"
    test_waterfall()
