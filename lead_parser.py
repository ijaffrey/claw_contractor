"""
Lead Parser Module
Extracts structured data from email bodies using Claude API
"""

import re
import json
from anthropic import Anthropic
from config import Config


def parse_lead(email_data):
    """
    Extract lead information from email using Claude API

    Args:
        email_data: Raw email data from Gmail API containing:
            - from: sender email/name
            - subject: email subject
            - body: email body text
            - headers: email headers

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
    if not email_data:
        return None

    # Extract basic info from email metadata
    from_header = email_data.get('from', '')
    subject = email_data.get('subject', '')
    body = email_data.get('body', '')

    # Parse customer email and name from "From" header
    customer_email, display_name = parse_from_header(from_header)

    # Detect source from email domain/headers
    source = detect_source(email_data)

    # Use Claude API to extract structured data from email content
    extracted_data = extract_with_claude(subject, body, display_name)

    # Combine all data
    lead_data = {
        'customer_name': extracted_data.get('customer_name') or display_name or 'Unknown',
        'customer_email': customer_email,
        'phone': extracted_data.get('phone'),
        'job_type': extracted_data.get('job_type'),
        'description': extracted_data.get('description') or body[:500],  # Fallback to body snippet
        'location': extracted_data.get('location'),
        'attachments': [],  # TODO: Extract attachments in future iteration
        'source': source,
        'urgency': extracted_data.get('urgency', 'normal'),
        'raw_subject': subject,
        'raw_body': body
    }

    return lead_data


def parse_from_header(from_header):
    """
    Parse email and display name from From header

    Examples:
        "John Smith <john@example.com>" -> ("john@example.com", "John Smith")
        "john@example.com" -> ("john@example.com", None)
    """
    # Match pattern: "Display Name <email@example.com>"
    match = re.match(r'^(.+?)\s*<(.+?)>$', from_header)

    if match:
        display_name = match.group(1).strip().strip('"')
        email = match.group(2).strip()
        return email, display_name
    else:
        # Just an email address
        return from_header.strip(), None


def extract_with_claude(subject, body, display_name):
    """
    Use Claude API to intelligently extract structured data from email

    Returns dict with:
        - customer_name
        - phone
        - job_type
        - description
        - location
        - urgency
    """
    client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    prompt = f"""You are a lead data extraction assistant for a plumbing business. Extract structured information from this customer inquiry email.

EMAIL SUBJECT: {subject}

EMAIL BODY:
{body}

SENDER NAME (if available): {display_name or 'Not provided'}

Extract the following information and return ONLY a valid JSON object with these exact keys:
{{
    "customer_name": "full name of customer (use sender name if not in body, or 'Unknown' if unclear)",
    "phone": "phone number if mentioned, otherwise null",
    "job_type": "brief categorization (e.g., 'leak repair', 'drain cleaning', 'installation', 'general inquiry')",
    "description": "1-2 sentence summary of what the customer needs",
    "location": "address or location if mentioned, otherwise null",
    "urgency": "emergency|urgent|soon|planning" (emergency=immediate, urgent=same day, soon=this week, planning=future)
}}

IMPORTANT: Return ONLY the JSON object, no other text."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse Claude's response
        response_text = message.content[0].text.strip()

        # Extract JSON from response (in case Claude adds extra text)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            return data
        else:
            # Fallback if no JSON found
            return parse_fallback(subject, body)

    except Exception as e:
        print(f"⚠ Claude API error: {e}")
        # Fallback to basic parsing
        return parse_fallback(subject, body)


def parse_fallback(subject, body):
    """
    Fallback parser using regex when Claude API is unavailable
    """
    # Extract phone number
    phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
    phone_match = re.search(phone_pattern, body)
    phone = phone_match.group(0) if phone_match else None

    # Detect urgency from keywords
    urgency = 'normal'
    if any(word in subject.lower() + ' ' + body.lower() for word in ['emergency', 'urgent', 'asap', 'immediately', 'flooding']):
        urgency = 'urgent'

    # Basic job type detection
    job_type = 'general inquiry'
    if 'leak' in subject.lower() + ' ' + body.lower():
        job_type = 'leak repair'
    elif 'drain' in subject.lower() + ' ' + body.lower():
        job_type = 'drain cleaning'
    elif 'install' in subject.lower() + ' ' + body.lower():
        job_type = 'installation'

    return {
        'customer_name': None,
        'phone': phone,
        'job_type': job_type,
        'description': body[:200],
        'location': None,
        'urgency': urgency
    }


def detect_source(email_data):
    """
    Detect lead source (Houzz, Angi, Thumbtack, direct, unknown)

    Checks email headers and sender domain to identify the source
    """
    from_header = email_data.get('from', '').lower()
    subject = email_data.get('subject', '').lower()
    headers = email_data.get('headers', [])

    # Check sender domain
    if 'houzz.com' in from_header or 'houzz' in subject:
        return 'Houzz'
    elif 'angi.com' in from_header or 'angieslist' in from_header or 'angi' in subject:
        return 'Angi'
    elif 'thumbtack.com' in from_header or 'thumbtack' in subject:
        return 'Thumbtack'
    elif 'homeadvisor.com' in from_header or 'homeadvisor' in subject:
        return 'HomeAdvisor'
    elif 'yelp.com' in from_header or 'yelp' in subject:
        return 'Yelp'

    # Check for forwarding headers (common in lead aggregators)
    for header in headers:
        header_name = header.get('name', '').lower()
        header_value = header.get('value', '').lower()

        if 'x-forwarded' in header_name or 'x-original-sender' in header_name:
            if 'houzz' in header_value:
                return 'Houzz'
            elif 'angi' in header_value or 'angieslist' in header_value:
                return 'Angi'
            elif 'thumbtack' in header_value:
                return 'Thumbtack'

    # If none of the above, it's a direct inquiry
    return 'Direct'


def extract_attachments(email_data):
    """
    Extract attachment information from email
    (Placeholder for future implementation)

    Returns list of attachment metadata
    """
    # TODO: Implement attachment extraction
    return []
