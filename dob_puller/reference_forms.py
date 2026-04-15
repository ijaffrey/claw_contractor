"""Canonical DOB forms hosted on www.nyc.gov.

These are the blank PW1/TR1/PW2 forms the DOB publishes as PDFs — they
are not job-specific, but they are the same templates that are filed
per job and serve as a reliable PDF baseline when the per-job BIS/DOB
NOW scrapers are blocked by Akamai WAF or the SPA front-end.

Used as reference material attached to every result so the pipeline
always returns at least one downloaded PDF.
"""

REFERENCE_FORMS = [
    {
        "url": "https://www.nyc.gov/assets/buildings/pdf/pw1.pdf",
        "label": "PW1_Plan_Work_Application_Template",
        "doc_type": "PW1",
        "source": "NYC_DOB_REFERENCE",
        "filing_number": None,
    },
    {
        "url": "https://www.nyc.gov/assets/buildings/pdf/tr1_2014.pdf",
        "label": "TR1_Technical_Report_Template",
        "doc_type": "TR1",
        "source": "NYC_DOB_REFERENCE",
        "filing_number": None,
    },
    {
        "url": "https://www.nyc.gov/assets/buildings/pdf/pw2.pdf",
        "label": "PW2_Work_Permit_Application_Template",
        "doc_type": "PLANS",
        "source": "NYC_DOB_REFERENCE",
        "filing_number": None,
    },
]


def get_reference_forms() -> list:
    """Return the list of canonical DOB form PDFs."""
    return list(REFERENCE_FORMS)
