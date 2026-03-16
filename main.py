"""
OpenClaw Trade Assistant - Main Entry Point
Orchestrates the full lead qualification loop
"""

import time
from datetime import datetime
from config import Config
import gmail_listener
import lead_parser
import reply_generator
import database as db
import conversation_manager as cm


def process_lead(email_data, business):
    """
    Process a single lead through the complete workflow
    Handles both new leads and replies to existing conversations

    Args:
        email_data: Email data from Gmail
        business: Business profile from database

    Returns:
        bool: True if processed successfully
    """
    try:
        # Check if this exact email was already processed
        existing_email = db.get_lead_by_email_id(email_data['id'])
        if existing_email:
            print(f"  ⊙ Already processed (Lead ID: {existing_email['id']})")
            return False

        # Check if this is a reply to an existing conversation
        existing_lead = db.get_lead_by_thread_id(email_data['thread_id'])

        if existing_lead:
            # This is a REPLY to an existing conversation
            return process_reply(email_data, existing_lead, business)
        else:
            # This is a NEW lead
            return process_new_lead(email_data, business)

    except Exception as e:
        print(f"  ✗ Error processing lead: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_new_lead(email_data, business):
    """
    Process a brand new lead (first contact)

    Args:
        email_data: Email data from Gmail
        business: Business profile from database

    Returns:
        bool: True if processed successfully
    """
    print(f"\n  📋 Parsing new lead data...")
    # Parse the lead
    lead_data = lead_parser.parse_lead(email_data)

    if not lead_data:
        print(f"  ✗ Failed to parse lead")
        return False

    print(f"     Customer: {lead_data['customer_name']}")
    print(f"     Job type: {lead_data['job_type']}")
    print(f"     Urgency:  {lead_data['urgency']}")
    print(f"     Source:   {lead_data['source']}")

    # Store in database
    print(f"  💾 Storing lead in database...")
    lead_record = {
        'business_id': business['id'],
        'customer_name': lead_data['customer_name'],
        'customer_email': lead_data['customer_email'],
        'phone': lead_data['phone'],
        'job_type': lead_data['job_type'],
        'description': lead_data['description'],
        'location': lead_data['location'],
        'source': lead_data['source'],
        'urgency': lead_data['urgency'],
        'status': 'new',
        'qualification_step': 1,
        'raw_subject': lead_data['raw_subject'],
        'raw_body': lead_data['raw_body'],
        'email_thread_id': email_data['thread_id'],
        'email_id': email_data['id']
    }

    saved_lead = db.insert_lead(lead_record)
    if not saved_lead:
        print(f"  ✗ Failed to save lead to database")
        return False

    # Store initial customer message in conversations
    print(f"  💬 Storing initial message in conversation history...")
    db.insert_conversation_message(
        lead_id=saved_lead['id'],
        role='customer',
        message=email_data['body'],
        email_id=email_data['id']
    )

    # Generate reply
    print(f"  🤖 Generating branded reply with Claude AI...")
    reply_text = reply_generator.generate_reply(lead_data, business)

    print(f"\n  {'─' * 56}")
    print(f"  REPLY:")
    print(f"  {'─' * 56}")
    # Indent the reply text
    for line in reply_text.split('\n'):
        print(f"  {line}")
    print(f"  {'─' * 56}")

    # Send reply
    print(f"\n  📤 Sending reply via Gmail...")
    sent_message = reply_generator.send_reply(email_data, reply_text)

    if not sent_message:
        print(f"  ✗ Failed to send reply")
        # Update status to 'failed' but keep the lead
        db.update_lead_status(saved_lead['id'], 'send_failed')
        return False

    # Store assistant's reply in conversations
    db.insert_conversation_message(
        lead_id=saved_lead['id'],
        role='assistant',
        message=reply_text,
        email_id=sent_message['id']
    )

    # Update lead status to 'contacted'
    print(f"  ✅ Updating lead status to 'contacted'...")
    db.update_lead_status(saved_lead['id'], 'contacted')

    print(f"\n  {'=' * 56}")
    print(f"  ✓ NEW LEAD PROCESSED SUCCESSFULLY")
    print(f"  {'=' * 56}")
    print(f"  Lead ID:     {saved_lead['id']}")
    print(f"  Status:      contacted")
    print(f"  Step:        1 (initial contact)")
    print(f"  Reply sent:  Yes")
    print(f"  {'=' * 56}\n")

    return True


def process_reply(email_data, lead, business):
    """
    Process a reply to an existing conversation

    Args:
        email_data: Email data from Gmail
        lead: Existing lead record
        business: Business profile from database

    Returns:
        bool: True if processed successfully
    """
    print(f"\n  💬 Processing REPLY to existing lead...")
    print(f"     Lead ID:  {lead['id']}")
    print(f"     Customer: {lead['customer_name']}")
    print(f"     Current step: {lead.get('qualification_step', 1)}")

    # Get customer's reply text
    customer_reply = email_data['body']

    # Store customer's reply in conversations
    print(f"  💾 Storing customer reply in conversation history...")
    db.insert_conversation_message(
        lead_id=lead['id'],
        role='customer',
        message=customer_reply,
        email_id=email_data['id']
    )

    # Load full conversation history
    print(f"  📜 Loading conversation history...")
    conversation_history = db.get_conversation_history(lead['id'])
    print(f"     Total messages: {len(conversation_history)}")

    # Determine next step
    current_step = lead.get('qualification_step', 1)
    next_step = cm.determine_next_step(lead, conversation_history, customer_reply)

    print(f"  🎯 Qualification sequence:")
    print(f"     Current step: {current_step} - {cm.get_step_info(current_step)['name']}")
    print(f"     Next step:    {next_step} - {cm.get_step_info(next_step)['name']}")

    # Generate contextual follow-up reply
    print(f"  🤖 Generating contextual follow-up with Claude AI...")
    reply_text = reply_generator.generate_follow_up_reply(
        lead, business, conversation_history, customer_reply
    )

    print(f"\n  {'─' * 56}")
    print(f"  FOLLOW-UP REPLY:")
    print(f"  {'─' * 56}")
    # Indent the reply text
    for line in reply_text.split('\n'):
        print(f"  {line}")
    print(f"  {'─' * 56}")

    # Send reply
    print(f"\n  📤 Sending follow-up reply via Gmail...")
    sent_message = reply_generator.send_reply(email_data, reply_text)

    if not sent_message:
        print(f"  ✗ Failed to send reply")
        return False

    # Store assistant's reply in conversations
    db.insert_conversation_message(
        lead_id=lead['id'],
        role='assistant',
        message=reply_text,
        email_id=sent_message['id']
    )

    # Update qualification step
    if next_step != current_step:
        print(f"  ⬆️  Advancing to qualification step {next_step}...")
        db.update_qualification_step(lead['id'], next_step)

        # Update status based on step
        if next_step == 6:
            db.update_lead_status(lead['id'], 'qualified')
        elif next_step > 1:
            db.update_lead_status(lead['id'], 'in_progress')

    print(f"\n  {'=' * 56}")
    print(f"  ✓ REPLY PROCESSED SUCCESSFULLY")
    print(f"  {'=' * 56}")
    print(f"  Lead ID:     {lead['id']}")
    print(f"  Step:        {next_step}/6")
    print(f"  Messages:    {len(conversation_history) + 2}")  # +2 for the new ones
    print(f"  Reply sent:  Yes")
    print(f"  {'=' * 56}\n")

    return True


def main():
    """
    Main loop that:
    1. Polls Gmail every 30 seconds
    2. Detects new leads
    3. Parses lead data
    4. Generates branded reply
    5. Sends reply via Gmail
    6. Stores lead record in Supabase
    """
    print("\n" + "=" * 60)
    print("🦞 OpenClaw Trade Assistant")
    print("=" * 60)
    print(f"Started:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Monitor email: {Config.GMAIL_USER_EMAIL}")
    print(f"Poll interval: {Config.POLL_INTERVAL_SECONDS} seconds")
    print("=" * 60)

    # Get business profile
    print("\n📊 Loading business profile from database...")
    businesses = db.get_all_businesses()

    if not businesses:
        print("✗ No business found in database!")
        print("Please run schema.sql to seed a business profile.")
        return

    business = businesses[0]
    print(f"✓ Business loaded: {business['name']}")
    print(f"  Trade type:    {business['trade_type']}")
    print(f"  Email:         {business['email']}")
    print(f"  Brand voice:   {business['brand_voice'][:50]}...")

    print("\n" + "=" * 60)
    print("🔄 Starting main loop...")
    print("=" * 60)
    print("Monitoring inbox for new leads...")
    print("(Press Ctrl+C to stop)\n")

    loop_count = 0

    try:
        while True:
            loop_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')

            print(f"[{timestamp}] Poll #{loop_count} - Checking inbox...")

            # Poll inbox for new leads
            try:
                leads = gmail_listener.poll_inbox()

                if not leads:
                    print(f"  → No new leads found")
                else:
                    print(f"  → Found {len(leads)} potential lead(s)")

                    for i, email_data in enumerate(leads, 1):
                        print(f"\n{'─' * 60}")
                        print(f"📧 LEAD #{i}: {email_data['subject']}")
                        print(f"{'─' * 60}")
                        print(f"  From:    {email_data['from']}")
                        print(f"  Date:    {email_data['date']}")

                        # Process the lead
                        process_lead(email_data, business)

            except Exception as e:
                print(f"  ✗ Error during poll: {e}")
                import traceback
                traceback.print_exc()

            # Wait before next poll
            print(f"\n⏳ Waiting {Config.POLL_INTERVAL_SECONDS} seconds until next check...")
            print("─" * 60 + "\n")
            time.sleep(Config.POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("⊗ Shutdown requested by user")
        print("=" * 60)
        print(f"Total polls completed: {loop_count}")
        print(f"Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
