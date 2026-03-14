"""
Reply Generator Module
Uses Claude API to generate branded responses to leads
"""

from config import Config


def generate_reply(lead_data, business_profile):
    """
    Generate a branded reply to a lead using Claude API

    Args:
        lead_data: Parsed lead information dictionary
        business_profile: Business information including brand_voice

    Returns:
        str: Generated reply text (under 100 words)
    """
    # TODO: Implement in Step 5
    pass


def send_reply(email_id, reply_text):
    """
    Send reply via Gmail API on the original thread

    Args:
        email_id: Original email ID to reply to
        reply_text: Generated reply text
    """
    # TODO: Implement in Step 6
    pass
