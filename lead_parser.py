"""
Lead Parser Module
Extracts structured data from email bodies
"""


def parse_lead(email_data):
    """
    Extract lead information from email

    Args:
        email_data: Raw email data from Gmail API

    Returns:
        dict: Structured lead data containing:
            - customer_name
            - customer_email
            - phone
            - job_type
            - description
            - location
            - attachments
            - source
    """
    # TODO: Implement in Step 3
    pass


def detect_source(email_data):
    """
    Detect lead source (Houzz, Angi, Thumbtack, direct, unknown)
    """
    # TODO: Implement in Step 3
    pass
