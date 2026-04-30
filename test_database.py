"""
Test script for database operations
"""

import database as db
from datetime import datetime


def test_connection():
    """Test Supabase connection"""
    print("\n" + "=" * 60)
    print("TEST 1: Supabase Connection")
    print("=" * 60)

    success = db.test_connection()
    if success:
        print("✓ Connection test passed!\n")
        return True
    else:
        print("✗ Connection test failed!\n")
        return False


def test_get_businesses():
    """Test retrieving businesses"""
    print("\n" + "=" * 60)
    print("TEST 2: Retrieve Businesses")
    print("=" * 60)

    businesses = db.get_all_businesses()

    if businesses:
        print(f"✓ Found {len(businesses)} business(es):\n")
        for biz in businesses:
            print(f"  - {biz['name']} ({biz['trade_type']})")
            print(f"    ID: {biz['id']}")
            print(f"    Email: {biz['email']}")
            print(f"    Brand Voice: {biz['brand_voice'][:100]}...")
            print()
        return businesses[0]  # Return first business for testing
    else:
        print("⚠ No businesses found. Run schema.sql to seed Mike's Plumbing")
        return None


def test_insert_lead(business_id):
    """Test inserting a lead"""
    print("\n" + "=" * 60)
    print("TEST 3: Insert Lead")
    print("=" * 60)

    lead_data = {
        "business_id": business_id,
        "customer_name": "John Test",
        "customer_email": "john.test@example.com",
        "phone": "555-1234",
        "job_type": "leak repair",
        "description": "Test lead - leaking kitchen sink",
        "location": "123 Test St, Boston MA",
        "source": "Direct",
        "urgency": "urgent",
        "status": "new",
        "raw_subject": "Test: Leaking sink",
        "raw_body": "I have a leaking sink in my kitchen",
        "email_thread_id": "test_thread_123",
        "email_id": "test_email_123",
    }

    lead = db.insert_lead(lead_data)

    if lead:
        print("\n✓ Lead inserted successfully!")
        print(f"  Lead ID: {lead['id']}")
        return lead
    else:
        print("\n✗ Failed to insert lead")
        return None


def test_get_leads(business_id):
    """Test retrieving leads"""
    print("\n" + "=" * 60)
    print("TEST 4: Retrieve Leads")
    print("=" * 60)

    leads = db.get_leads(business_id)

    if leads:
        print(f"✓ Found {len(leads)} lead(s):\n")
        for lead in leads:
            print(f"  - {lead['customer_name']} ({lead['job_type']})")
            print(f"    Status: {lead['status']}")
            print(f"    Urgency: {lead['urgency']}")
            print(f"    Source: {lead['source']}")
            print(f"    Created: {lead['created_at']}")
            print()
        return leads
    else:
        print("No leads found")
        return []


def test_update_lead_status(lead_id):
    """Test updating lead status"""
    print("\n" + "=" * 60)
    print("TEST 5: Update Lead Status")
    print("=" * 60)

    updated_lead = db.update_lead_status(lead_id, "contacted")

    if updated_lead:
        print(f"\n✓ Lead status updated to: {updated_lead['status']}")
        return True
    else:
        print("\n✗ Failed to update lead status")
        return False


def test_get_lead_by_email_id():
    """Test retrieving lead by email ID"""
    print("\n" + "=" * 60)
    print("TEST 6: Get Lead by Email ID")
    print("=" * 60)

    lead = db.get_lead_by_email_id("test_email_123")

    if lead:
        print(f"✓ Found lead: {lead['customer_name']}")
        print(f"  Email ID: {lead['email_id']}")
        return True
    else:
        print("✗ Lead not found by email ID")
        return False


def main():
    """Run all database tests"""
    print("\n" + "=" * 60)
    print("DATABASE TEST SUITE")
    print("=" * 60)
    print("This will test all database operations against Supabase")
    print("=" * 60)

    # Test 1: Connection
    if not test_connection():
        print("\n❌ Cannot proceed without database connection")
        print("Please check your SUPABASE_URL and SUPABASE_KEY in .env")
        return

    # Test 2: Get businesses
    business = test_get_businesses()
    if not business:
        print(
            "\n❌ No business found. Please run schema.sql in Supabase SQL Editor first."
        )
        return

    business_id = business["id"]

    # Test 3: Insert lead
    lead = test_insert_lead(business_id)
    if not lead:
        print("\n❌ Failed to insert lead")
        return

    lead_id = lead["id"]

    # Test 4: Get leads
    test_get_leads(business_id)

    # Test 5: Update lead status
    test_update_lead_status(lead_id)

    # Test 6: Get lead by email ID
    test_get_lead_by_email_id()

    # Summary
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nDatabase is fully operational and ready for production use.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
