"""
Test script for Gmail Listener
Demonstrates OAuth authentication and email polling
"""

import time
from gmail_listener import authenticate_gmail, poll_inbox


def test_authentication():
    """Test Gmail OAuth authentication"""
    print("\n" + "=" * 60)
    print("TEST 1: Gmail Authentication")
    print("=" * 60)

    try:
        service = authenticate_gmail()
        print("✓ Authentication test passed!")
        return True
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return False


def test_poll_inbox():
    """Test polling inbox for new leads"""
    print("\n" + "=" * 60)
    print("TEST 2: Poll Inbox for New Leads")
    print("=" * 60)

    try:
        leads = poll_inbox()

        if not leads:
            print("No new leads found in inbox")
            print("\nTIP: To test this properly:")
            print("1. Send yourself a test email with subject: 'Need plumbing repair'")
            print("2. Leave it unread")
            print("3. Run this test again")
        else:
            print(f"\nFound {len(leads)} potential lead(s):")
            for i, lead in enumerate(leads, 1):
                print(f"\nLead #{i}:")
                print(f"  From:    {lead['from']}")
                print(f"  Subject: {lead['subject']}")
                print(f"  Date:    {lead['date']}")
                print(f"  Preview: {lead['snippet'][:100]}...")

        print("\n✓ Poll inbox test passed!")
        return True

    except Exception as e:
        print(f"✗ Poll inbox failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_continuous_polling():
    """Test continuous polling (runs for 2 minutes)"""
    print("\n" + "=" * 60)
    print("TEST 3: Continuous Polling (2 minutes)")
    print("=" * 60)
    print("Checking inbox every 10 seconds...")
    print("Send yourself a test email to see real-time detection!")
    print("(Press Ctrl+C to stop)\n")

    try:
        for i in range(12):  # 12 checks over 2 minutes
            print(f"[{i+1}/12] Checking inbox at {time.strftime('%H:%M:%S')}...")
            leads = poll_inbox()

            if leads:
                print(f"  → Found {len(leads)} new lead(s)!")
            else:
                print("  → No new leads")

            if i < 11:  # Don't sleep on last iteration
                time.sleep(10)

        print("\n✓ Continuous polling test completed!")
        return True

    except KeyboardInterrupt:
        print("\n\n✓ Test stopped by user")
        return True
    except Exception as e:
        print(f"\n✗ Continuous polling failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("GMAIL LISTENER TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Authentication
    results.append(("Authentication", test_authentication()))

    # Test 2: Poll inbox once
    results.append(("Poll Inbox", test_poll_inbox()))

    # Ask if user wants to test continuous polling
    print("\n" + "-" * 60)
    response = input("Run continuous polling test? (y/n): ").strip().lower()
    if response == "y":
        results.append(("Continuous Polling", test_continuous_polling()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20} {status}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
