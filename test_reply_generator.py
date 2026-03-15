"""
Test script for Reply Generator
Demonstrates branded reply generation with Claude API
"""

import database as db
from reply_generator import generate_reply


def test_reply_generation():
    """Test reply generation with various lead scenarios"""
    print("\n" + "=" * 60)
    print("REPLY GENERATOR TEST")
    print("=" * 60)

    # Get business profile from database
    print("\nFetching business profile from database...")
    businesses = db.get_all_businesses()

    if not businesses:
        print("✗ No business found in database")
        print("Please run schema.sql to seed Mike's Plumbing")
        return

    business = businesses[0]
    print(f"✓ Using business: {business['name']}")
    print(f"  Brand voice: {business['brand_voice'][:60]}...")

    # Test scenarios
    test_leads = [
        {
            'name': 'Emergency - Flooded Basement',
            'lead_data': {
                'customer_name': 'John Smith',
                'customer_email': 'john@example.com',
                'job_type': 'leak repair',
                'description': 'Burst pipe flooding my basement',
                'urgency': 'emergency',
                'location': '123 Oak Street, Boston MA',
                'phone': '617-555-1234'
            }
        },
        {
            'name': 'Urgent - Kitchen Sink Leak',
            'lead_data': {
                'customer_name': 'Sarah Johnson',
                'customer_email': 'sarah@example.com',
                'job_type': 'leak repair',
                'description': 'Leaking kitchen sink, water pooling on floor',
                'urgency': 'urgent',
                'location': None,
                'phone': None
            }
        },
        {
            'name': 'Normal - Bathroom Installation',
            'lead_data': {
                'customer_name': 'Mike Chen',
                'customer_email': 'mike@example.com',
                'job_type': 'installation',
                'description': 'Need to install new bathroom fixtures in basement',
                'urgency': 'planning',
                'location': '456 Maple Ave, Cambridge MA',
                'phone': '555-987-6543'
            }
        },
        {
            'name': 'Drain Cleaning Request',
            'lead_data': {
                'customer_name': 'Lisa Williams',
                'customer_email': 'lisa@example.com',
                'job_type': 'drain cleaning',
                'description': 'Slow draining bathroom sink',
                'urgency': 'soon',
                'location': None,
                'phone': None
            }
        }
    ]

    # Generate replies for each scenario
    for i, scenario in enumerate(test_leads, 1):
        print("\n" + "=" * 60)
        print(f"SCENARIO #{i}: {scenario['name']}")
        print("=" * 60)

        lead_data = scenario['lead_data']

        print(f"\nLead Details:")
        print(f"  Customer: {lead_data['customer_name']}")
        print(f"  Job Type: {lead_data['job_type']}")
        print(f"  Urgency: {lead_data['urgency']}")
        print(f"  Description: {lead_data['description']}")
        if lead_data['location']:
            print(f"  Location: {lead_data['location']}")

        print(f"\nGenerating branded reply with Claude API...")

        reply = generate_reply(lead_data, business)

        # Count words
        word_count = len(reply.split())

        print(f"\n{'─' * 60}")
        print("GENERATED REPLY:")
        print(f"{'─' * 60}")
        print(reply)
        print(f"{'─' * 60}")
        print(f"Word count: {word_count} words")

        if word_count <= 100:
            print("✓ Within 100 word limit")
        else:
            print("⚠ Exceeds 100 word limit")


def test_with_real_leads():
    """Test with actual leads from inbox"""
    print("\n" + "=" * 60)
    print("TEST WITH REAL LEADS FROM INBOX")
    print("=" * 60)

    # Get business
    businesses = db.get_all_businesses()
    if not businesses:
        print("✗ No business found")
        return

    business = businesses[0]
    print(f"\n✓ Using business: {business['name']}")

    # Get leads from database
    leads = db.get_leads(business['id'], limit=5)

    if not leads:
        print("\n⚠ No leads in database yet")
        print("Run the full pipeline to import leads from Gmail")
        return

    print(f"\n✓ Found {len(leads)} lead(s) in database\n")

    for i, lead in enumerate(leads, 1):
        print(f"\n{'=' * 60}")
        print(f"LEAD #{i}: {lead['customer_name']} - {lead['job_type']}")
        print(f"{'=' * 60}")

        print(f"  Description: {lead['description']}")
        print(f"  Urgency: {lead['urgency']}")
        print(f"  Status: {lead['status']}")

        print(f"\nGenerating reply...")

        reply = generate_reply(lead, business)

        print(f"\n{'─' * 60}")
        print("GENERATED REPLY:")
        print(f"{'─' * 60}")
        print(reply)
        print(f"{'─' * 60}")

        word_count = len(reply.split())
        print(f"Word count: {word_count} words")


def main():
    """Run reply generator tests"""
    import sys

    print("\n" + "=" * 60)
    print("REPLY GENERATOR TEST SUITE")
    print("=" * 60)
    print("\nChoose test mode:")
    print("1. Test with sample scenarios (4 different lead types)")
    print("2. Test with real leads from database")
    print("3. Both")

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        try:
            choice = input("\nEnter choice (1/2/3): ").strip()
        except EOFError:
            choice = "1"  # Default to sample scenarios

    if choice == "1":
        test_reply_generation()
    elif choice == "2":
        test_with_real_leads()
    elif choice == "3":
        test_reply_generation()
        test_with_real_leads()
    else:
        print("Invalid choice. Running sample scenarios...")
        test_reply_generation()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
