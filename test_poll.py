"""
Simple test to poll inbox for leads
"""

from gmail_listener import poll_inbox

print("\n" + "=" * 60)
print("POLLING INBOX FOR NEW LEADS")
print("=" * 60)

leads = poll_inbox()

if not leads:
    print("\n❌ No new leads found in inbox")
    print("\nTo test lead detection:")
    print("1. Send an email to ijaffreybetatest@gmail.com")
    print("2. Subject: 'Need urgent plumbing repair - leaking pipe'")
    print("3. Body: 'Hi, I have a leaking pipe in my basement. Can you help?'")
    print("4. Leave it UNREAD")
    print("5. Run this test again: python3 test_poll.py")
else:
    print(f"\n✓ Found {len(leads)} potential lead(s)!\n")

    for i, lead in enumerate(leads, 1):
        print(f"{'=' * 60}")
        print(f"LEAD #{i}")
        print(f"{'=' * 60}")
        print(f"From:       {lead['from']}")
        print(f"Subject:    {lead['subject']}")
        print(f"Date:       {lead['date']}")
        print(f"Thread ID:  {lead['thread_id']}")
        print(f"Email ID:   {lead['id']}")
        print(f"\nBody Preview:")
        print("-" * 60)
        print(lead["body"][:300] + "..." if len(lead["body"]) > 300 else lead["body"])
        print("-" * 60)
        print()

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60 + "\n")
