"""
Gmail Listener Module
Handles Gmail OAuth2 authentication and email polling
"""

import os
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import Config


# Global service instance
_gmail_service = None


def authenticate_gmail():
    """
    Authenticate with Gmail using OAuth2
    Returns authenticated Gmail service

    In production (Railway): Uses GMAIL_TOKEN_JSON environment variable
    Locally: Uses token.json file or prompts for OAuth if needed
    """
    global _gmail_service

    if _gmail_service:
        return _gmail_service

    creds = None

    # Check for environment variable (Railway/production)
    gmail_token_json = os.getenv('GMAIL_TOKEN_JSON')

    if gmail_token_json:
        # Production mode: Load from environment variable
        print("Loading Gmail credentials from GMAIL_TOKEN_JSON environment variable...")
        try:
            token_data = json.loads(gmail_token_json)
            creds = Credentials.from_authorized_user_info(token_data, Config.GMAIL_SCOPES)
            print("✓ Gmail token loaded from environment")
        except Exception as e:
            print(f"✗ Error parsing GMAIL_TOKEN_JSON: {e}")
            raise RuntimeError("Invalid GMAIL_TOKEN_JSON environment variable")
    else:
        # Local development mode: Use token.json file
        token_path = 'token.json'

        if os.path.exists(token_path):
            print(f"Loading Gmail credentials from {token_path}...")
            creds = Credentials.from_authorized_user_file(token_path, Config.GMAIL_SCOPES)
        else:
            # Check if we're running on Railway (headless environment)
            if os.getenv('RAILWAY_ENVIRONMENT'):
                raise RuntimeError(
                    "No valid Gmail token found. "
                    "Please set GMAIL_TOKEN_JSON environment variable in Railway. "
                    "Generate token locally with: python3 test_gmail_listener.py"
                )

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        print("Token expired. Refreshing...")
        try:
            creds.refresh(Request())
            print("✓ Token refreshed successfully")

            # Save refreshed token back to file (local only)
            if not os.getenv('GMAIL_TOKEN_JSON') and os.path.exists('token.json'):
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
                print("✓ Refreshed token saved to token.json")
        except Exception as e:
            print(f"✗ Token refresh failed: {e}")
            raise RuntimeError("Failed to refresh Gmail token. Please regenerate token locally.")

    # If still no valid credentials, try interactive OAuth (local only)
    if not creds or not creds.valid:
        # Check if we're in a headless environment
        if os.getenv('RAILWAY_ENVIRONMENT'):
            raise RuntimeError(
                "No valid Gmail token found. "
                "Cannot run interactive OAuth on Railway. "
                "Please set GMAIL_TOKEN_JSON environment variable."
            )

        # Local development: Run interactive OAuth
        print("\n" + "=" * 60)
        print("FIRST TIME SETUP: Gmail OAuth Authentication")
        print("=" * 60)
        print("A browser window will open for you to authorize access.")
        print("Sign in with:", Config.GMAIL_USER_EMAIL)
        print("-" * 60)

        client_config = {
            "installed": {
                "client_id": Config.GMAIL_CLIENT_ID,
                "client_secret": Config.GMAIL_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"]
            }
        }

        flow = InstalledAppFlow.from_client_config(client_config, Config.GMAIL_SCOPES)
        creds = flow.run_local_server(port=0)
        print("✓ Authentication successful!")

        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print(f"✓ Token saved to token.json")

    # Build Gmail service
    _gmail_service = build('gmail', 'v1', credentials=creds)
    print("✓ Gmail service initialized")

    return _gmail_service


def poll_inbox():
    """
    Poll Gmail inbox for new unread emails
    Filters out spam, auto-replies, and non-lead emails
    Returns list of new lead emails with metadata
    """
    service = authenticate_gmail()

    try:
        # Query for unread messages in inbox (not spam/trash)
        query = 'is:unread in:inbox -from:noreply -from:no-reply'

        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=10
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            return []

        # Fetch full details for each message
        lead_emails = []
        for msg in messages:
            email_data = get_email_details(service, msg['id'])

            # Filter out auto-replies and non-lead emails
            if not is_auto_reply(email_data) and is_potential_lead(email_data):
                lead_emails.append(email_data)
                log_detected_email(email_data)

        return lead_emails

    except HttpError as error:
        print(f"✗ Gmail API error: {error}")
        return []


def get_email_details(service, email_id):
    """
    Fetch full email details including headers and body

    Returns:
        dict with id, thread_id, from, subject, date, body, snippet
    """
    try:
        message = service.users().messages().get(
            userId='me',
            id=email_id,
            format='full'
        ).execute()

        headers = message['payload']['headers']

        # Extract key headers
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(No Subject)')
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
        date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

        # Extract email body (simplified - handles plain text)
        body = ''
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    import base64
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            import base64
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

        return {
            'id': email_id,
            'thread_id': message['threadId'],
            'from': from_header,
            'subject': subject,
            'date': date_header,
            'body': body or message.get('snippet', ''),
            'snippet': message.get('snippet', ''),
            'headers': headers
        }

    except HttpError as error:
        print(f"✗ Error fetching email {email_id}: {error}")
        return None


def is_auto_reply(email_data):
    """
    Detect auto-replies and automated messages

    Checks for:
    - Auto-reply headers
    - Out-of-office messages
    - Delivery failure notifications
    """
    if not email_data:
        return True

    headers = email_data.get('headers', [])
    subject = email_data.get('subject', '').lower()
    from_addr = email_data.get('from', '').lower()

    # Check for auto-reply headers
    auto_reply_headers = [
        'auto-submitted',
        'x-autoreply',
        'x-autorespond',
        'precedence'
    ]

    for header in headers:
        if header['name'].lower() in auto_reply_headers:
            return True

    # Check subject line for auto-reply indicators
    auto_reply_keywords = [
        'out of office',
        'automatic reply',
        'auto-reply',
        'autoresponder',
        'vacation reply',
        'delivery status notification',
        'undeliverable',
        'mailer-daemon'
    ]

    if any(keyword in subject for keyword in auto_reply_keywords):
        return True

    # Check sender for common auto-reply addresses
    if 'mailer-daemon' in from_addr or 'postmaster' in from_addr:
        return True

    return False


def is_potential_lead(email_data):
    """
    Determine if email is a potential lead

    Filters out:
    - Marketing emails
    - Newsletters
    - Social media notifications
    """
    if not email_data:
        return False

    subject = email_data.get('subject', '').lower()
    from_addr = email_data.get('from', '').lower()
    body = email_data.get('body', '').lower()

    # Filter out common non-lead patterns
    spam_keywords = [
        'unsubscribe',
        'newsletter',
        'promotion',
        'special offer',
        'click here',
        'limited time'
    ]

    # If subject/body contains spam keywords, likely not a lead
    spam_score = sum(1 for keyword in spam_keywords if keyword in subject or keyword in body)
    if spam_score >= 2:
        return False

    # Positive signals for leads (mentioning services, asking questions)
    lead_signals = [
        'quote',
        'estimate',
        'repair',
        'fix',
        'install',
        'service',
        'help',
        'need',
        'urgent',
        'emergency',
        'plumbing',
        'plumber',
        'leak',
        'drain',
        'water',
        'toilet',
        'sink',
        'pipe'
    ]

    # At least one lead signal is a good indicator
    has_lead_signal = any(signal in subject + ' ' + body for signal in lead_signals)

    return has_lead_signal


def log_detected_email(email_data):
    """
    Log detected email with timestamp, sender, and subject
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sender = email_data.get('from', 'Unknown')
    subject = email_data.get('subject', '(No Subject)')

    print(f"\n{'='*60}")
    print(f"📧 NEW LEAD DETECTED")
    print(f"{'='*60}")
    print(f"Timestamp: {timestamp}")
    print(f"From:      {sender}")
    print(f"Subject:   {subject}")
    print(f"{'='*60}\n")


def mark_as_read(email_id):
    """
    Mark an email as read by removing the UNREAD label
    """
    service = authenticate_gmail()

    try:
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

        print(f"✓ Marked email {email_id} as read")
        return True

    except HttpError as error:
        print(f"✗ Error marking email as read: {error}")
        return False


def get_service():
    """
    Get or create the Gmail service instance
    Useful for other modules that need direct access
    """
    return authenticate_gmail()
