"""
Test script for sending Gmail replies
CAUTION: This will send REAL emails when run in live mode
"""

import database as db
from gmail_listener import poll_inbox
from reply_generator import generate_reply, send_reply


def test_send_reply_dry_run():
    """
    Test reply sending in DRY RUN mode (shows what would be sent, doesn't actually send)
    """
    print("\n" + "=" * 60)
    print("SEND REPLY TEST - DRY RUN MODE")
    print("=" * 60)
    print("⚠  This is a DRY RUN - no emails will actually be sent")
    print("=" * 60)

    # Get business profile
    print("\nFetching business profile...")
    businesses = db.get_all_businesses()
    if not businesses:
        print("✗ No business found in database")
        return

    business = businesses[0]
    print(f"✓ Using business: {business['name']}")

    # Get a lead from inbox
    print("\nFetching leads from inbox...")
    leads = poll_inbox()

    if not leads:
        print("\n⚠ No unread leads found in inbox")
        print("\nTo test:")
        print("1. Send yourself a test email to: ijaffreybetatest@gmail.com")
        print("2. Subject: 'Test - Need plumbing help'")
        print("3. Body: 'I have a leaking faucet'")
        print("4. Leave it UNREAD")
        print("5. Run this test again")
        return

    # Use first lead
    email_data = leads[0]
    print(f"\n✓ Found lead from: {email_data['from']}")
    print(f"  Subject: {email_data['subject']}")

    # Parse lead
    from lead_parser import parse_lead
    lead_data = parse_lead(email_data)

    print(f"\nParsed lead data:")
    print(f"  Customer: {lead_data['customer_name']}")
    print(f"  Job type: {lead_data['job_type']}")
    print(f"  Urgency: {lead_data['urgency']}")

    # Generate reply
    print(f"\nGenerating reply...")
    reply_text = generate_reply(lead_data, business)

    print(f"\n{'─' * 60}")
    print("GENERATED REPLY:")
    print(f"{'─' * 60}")
    print(reply_text)
    print(f"{'─' * 60}")

    # Show what would be sent
    print(f"\n{'=' * 60}")
    print("DRY RUN - WHAT WOULD BE SENT:")
    print(f"{'=' * 60}")
    print(f"To:      {email_data['from']}")
    print(f"Subject: Re: {email_data['subject']}")
    print(f"Thread:  {email_data['thread_id']}")
    print(f"\nBody:\n{reply_text}")
    print(f"{'=' * 60}")
    print("\n⚠  No email was actually sent (DRY RUN mode)")


def test_send_reply_live():
    """
    Test reply sending in LIVE mode (ACTUALLY SENDS EMAIL)
    """
    print("\n" + "=" * 60)
    print("⚠⚠⚠  SEND REPLY TEST - LIVE MODE  ⚠⚠⚠")
    print("=" * 60)
    print("WARNING: This will send a REAL email!")
    print("=" * 60)

    # Confirmation prompt
    print("\nThis test will:")
    print("1. Find an unread email in your inbox")
    print("2. Generate a reply using Claude AI")
    print("3. ACTUALLY SEND the reply via Gmail")
    print("4. Mark the original email as read")

    response = input("\n⚠  Are you SURE you want to send a real email? (type 'YES' to confirm): ").strip()

    if response != 'YES':
        print("\n✓ Test cancelled. No emails sent.")
        return

    print("\n" + "=" * 60)
    print("PROCEEDING WITH LIVE EMAIL SEND")
    print("=" * 60)

    # Get business profile
    print("\nFetching business profile...")
    businesses = db.get_all_businesses()
    if not businesses:
        print("✗ No business found in database")
        return

    business = businesses[0]
    print(f"✓ Using business: {business['name']}")

    # Get a lead from inbox
    print("\nFetching leads from inbox...")
    leads = poll_inbox()

    if not leads:
        print("\n✗ No unread leads found in inbox")
        print("Send yourself a test email first")
        return

    # Use first lead
    email_data = leads[0]
    print(f"\n✓ Found lead from: {email_data['from']}")
    print(f"  Subject: {email_data['subject']}")

    # Parse lead
    from lead_parser import parse_lead
    lead_data = parse_lead(email_data)

    print(f"\nParsed lead data:")
    print(f"  Customer: {lead_data['customer_name']}")
    print(f"  Job type: {lead_data['job_type']}")
    print(f"  Urgency: {lead_data['urgency']}")

    # Generate reply
    print(f"\nGenerating reply with Claude API...")
    reply_text = generate_reply(lead_data, business)

    print(f"\n{'─' * 60}")
    print("REPLY TO BE SENT:")
    print(f"{'─' * 60}")
    print(reply_text)
    print(f"{'─' * 60}")

    # Final confirmation
    print(f"\nReady to send to: {email_data['from']}")
    final_confirm = input("Send this email? (type 'SEND' to confirm): ").strip()

    if final_confirm != 'SEND':
        print("\n✓ Send cancelled.")
        return

    # SEND THE EMAIL
    print(f"\n📤 Sending reply...")
    sent_message = send_reply(email_data, reply_text)

    if sent_message:
        print(f"\n{'=' * 60}")
        print("✓ EMAIL SENT SUCCESSFULLY!")
        print(f"{'=' * 60}")
        print(f"Sent message ID: {sent_message['id']}")
        print(f"Thread ID: {sent_message['threadId']}")
        print(f"\nCheck your sent folder in Gmail to verify!")
        print(f"{'=' * 60}")
    else:
        print("\n✗ Failed to send email")


def main():
    """Run send reply tests"""
    import sys

    print("\n" + "=" * 60)
    print("SEND REPLY TEST SUITE")
    print("=" * 60)
    print("\nChoose test mode:")
    print("1. Dry run (show what would be sent, don't actually send)")
    print("2. Live mode (ACTUALLY SEND EMAIL - use with caution!)")

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        try:
            choice = input("\nEnter choice (1/2): ").strip()
        except EOFError:
            choice = "1"  # Default to dry run

    if choice == "1":
        test_send_reply_dry_run()
    elif choice == "2":
        test_send_reply_live()
    else:
        print("Invalid choice. Running dry run...")
        test_send_reply_dry_run()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
