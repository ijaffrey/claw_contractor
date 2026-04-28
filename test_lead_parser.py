"""
Test script for Lead Parser
Demonstrates parsing structured data from emails
"""

import json
from gmail_listener import poll_inbox
from lead_parser import parse_lead


def test_parse_sample_leads():
    """Test parsing with sample email data"""
    print("\n" + "=" * 60)
    print("LEAD PARSER TEST")
    print("=" * 60)

    # Sample test data (in case no emails in inbox)
    sample_emails = [
        {
            "from": "John Smith <john.smith@example.com>",
            "subject": "Urgent - Leaking pipe in kitchen",
            "body": """Hi Mike,

I have a leaking pipe under my kitchen sink that's getting worse. Water is starting to pool on the floor. Can you come take a look today?

My address is 123 Oak Street, Boston MA.
You can reach me at 617-555-1234.

Thanks,
John Smith""",
            "headers": [],
        },
        {
            "from": "leads@thumbtack.com",
            "subject": "New Lead: Bathroom Installation",
            "body": """New lead from Thumbtack:

Customer: Sarah Johnson
Phone: (555) 987-6543
Project: Install new bathroom fixtures
Description: Need to install a new toilet, sink, and shower in our basement bathroom. Looking to get this done in the next 2-3 weeks.
Location: 456 Maple Ave, Cambridge MA""",
            "headers": [{"name": "X-Forwarded-From", "value": "thumbtack.com"}],
        },
        {
            "from": "emergency@homeowner.com",
            "subject": "EMERGENCY - Basement flooding",
            "body": """URGENT!!! My basement is flooding from a burst pipe. Water everywhere. Need someone NOW!

Call me ASAP: 555-2468

Address: 789 Pine Road""",
            "headers": [],
        },
    ]

    print("\n📋 Testing with sample email data...\n")

    for i, email in enumerate(sample_emails, 1):
        print(f"\n{'=' * 60}")
        print(f"SAMPLE EMAIL #{i}")
        print(f"{'=' * 60}")
        print(f"From:    {email['from']}")
        print(f"Subject: {email['subject']}")
        print(f"\nParsing...")

        parsed = parse_lead(email)

        print(f"\n✓ PARSED DATA:")
        print(json.dumps(parsed, indent=2, default=str))


def test_parse_real_leads():
    """Test parsing with real emails from inbox"""
    print("\n" + "=" * 60)
    print("PARSING REAL LEADS FROM INBOX")
    print("=" * 60)

    print("\nFetching leads from inbox...")
    leads = poll_inbox()

    if not leads:
        print("\n❌ No leads found in inbox")
        print("Run test_parse_sample_leads() instead to see sample parsing")
        return

    print(f"\n✓ Found {len(leads)} lead(s) to parse\n")

    for i, email_data in enumerate(leads, 1):
        print(f"\n{'=' * 60}")
        print(f"REAL LEAD #{i}")
        print(f"{'=' * 60}")
        print(f"From:    {email_data['from']}")
        print(f"Subject: {email_data['subject']}")
        print(f"\nParsing with Claude API...")

        parsed = parse_lead(email_data)

        print(f"\n✓ PARSED DATA:")
        print("-" * 60)
        print(f"Customer Name:  {parsed['customer_name']}")
        print(f"Email:          {parsed['customer_email']}")
        print(f"Phone:          {parsed['phone'] or 'Not provided'}")
        print(f"Job Type:       {parsed['job_type']}")
        print(f"Description:    {parsed['description']}")
        print(f"Location:       {parsed['location'] or 'Not provided'}")
        print(f"Source:         {parsed['source']}")
        print(f"Urgency:        {parsed['urgency']}")
        print("-" * 60)


def main():
    """Run all tests"""
    import sys

    print("\n" + "=" * 60)
    print("LEAD PARSER TEST SUITE")
    print("=" * 60)
    print("\nChoose test mode:")
    print("1. Parse sample emails (works without Anthropic API key)")
    print("2. Parse real emails from inbox (requires Anthropic API key)")
    print("3. Both")

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        try:
            choice = input("\nEnter choice (1/2/3): ").strip()
        except EOFError:
            choice = "2"  # Default to real emails when run in background

    if choice == "1":
        test_parse_sample_leads()
    elif choice == "2":
        test_parse_real_leads()
    elif choice == "3":
        test_parse_sample_leads()
        test_parse_real_leads()
    else:
        print("Invalid choice. Defaulting to real emails...")
        test_parse_real_leads()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
