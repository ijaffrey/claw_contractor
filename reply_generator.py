"""
Reply Generator Module
Uses Claude API to generate branded responses to leads
"""

from anthropic import Anthropic
from config import Config
import conversation_manager as cm


def generate_reply(lead_data, business_profile):
    """
    Generate a branded reply to a lead using Claude API

    Args:
        lead_data: Parsed lead information dictionary with:
            - customer_name
            - job_type
            - description
            - urgency
            - location (optional)
        business_profile: Business information dictionary with:
            - name
            - trade_type
            - brand_voice
            - phone (optional)

    Returns:
        str: Generated reply text (under 100 words)
    """
    client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    # Extract key information
    customer_name = lead_data.get('customer_name', 'there')
    job_type = lead_data.get('job_type', 'your request')
    description = lead_data.get('description', '')
    urgency = lead_data.get('urgency', 'normal')
    location = lead_data.get('location')

    business_name = business_profile.get('name', 'Our Team')
    brand_voice = business_profile.get('brand_voice', 'Friendly and professional')
    business_phone = business_profile.get('phone')

    # Build the prompt for Claude
    prompt = f"""You are writing a reply email on behalf of "{business_name}", a plumbing business.

BRAND VOICE:
{brand_voice}

CUSTOMER INFORMATION:
- Name: {customer_name}
- Issue: {job_type}
- Description: {description}
- Urgency level: {urgency}
{f'- Location: {location}' if location else ''}

YOUR TASK:
Write a warm, personalized reply email that:
1. Greets the customer by name
2. Acknowledges their specific issue ({job_type})
3. Shows you understand the urgency
4. Asks EXACTLY ONE qualifying question to collect information (NOT to commit to specific times):
   - For urgent/emergency: Ask for their preferred times/availability (e.g., "What times work best for you today? Share your availability and we'll follow up to coordinate.")
   - For normal requests: Ask about their general timing preference (e.g., "What days or times typically work best for you? Let us know and we'll be in touch to schedule.")
   - For leak repairs: Ask about severity (e.g., "Is the leak currently causing water damage, or is it a slow drip?")
   - For installations: Ask about their preferred timeline (e.g., "What timeframe are you thinking? Share what works for you and we'll reach out to coordinate.")
5. Keep it UNDER 100 words
6. Sound human and conversational, not robotic
7. Match the brand voice above
8. Do NOT include a signature (we'll add that separately)

CRITICAL RULES:
- NEVER promise specific availability or commit to specific times (e.g., don't say "we can come this afternoon", "we're available tomorrow", "we'll get someone out today", "I'll have someone call you")
- NEVER say WHEN you'll respond or follow up (e.g., don't say "I'll call you in 15 minutes", "we'll get back to you shortly", "soon", "right away", "quickly")
- Instead, use neutral language like "we'll follow up to coordinate", "we'll be in touch to schedule", "we'll reach out to confirm"
- ALWAYS ASK for the customer's preferred times/availability FIRST, then say you'll coordinate
- The contractor (not the AI) confirms all appointments and timing
- Only ask ONE question
- Keep it friendly and natural
- Don't use overly formal language
- Don't apologize excessively
- Get straight to the point

Write ONLY the email body, nothing else:"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        reply_body = message.content[0].text.strip()

        # Add signature
        signature = f"\n\n- {business_name}"
        if business_phone:
            signature += f"\n{business_phone}"

        full_reply = reply_body + signature

        return full_reply

    except Exception as e:
        print(f"✗ Error generating reply with Claude: {e}")
        # Fallback to template-based reply
        return generate_fallback_reply(lead_data, business_profile)


def generate_fallback_reply(lead_data, business_profile):
    """
    Fallback template-based reply if Claude API fails

    Args:
        lead_data: Parsed lead information
        business_profile: Business information

    Returns:
        str: Template-based reply
    """
    customer_name = lead_data.get('customer_name', 'there')
    job_type = lead_data.get('job_type', 'your plumbing issue')
    urgency = lead_data.get('urgency', 'normal')
    business_name = business_profile.get('name', 'Our Team')
    business_phone = business_profile.get('phone')

    # Select question based on urgency - collect customer's preferred times
    if urgency == 'emergency':
        question = "What times work best for you today? Share your availability and we'll follow up to coordinate."
    elif urgency == 'urgent':
        question = "What times work best for you over the next day or two? Let us know and we'll be in touch to schedule."
    else:
        question = "What days or times typically work best for you? Share what works for you and we'll reach out to coordinate."

    reply = f"Hi {customer_name}!\n\n"
    reply += f"Thanks for reaching out about the {job_type}. We can definitely help with that.\n\n"
    reply += f"{question}\n\n"
    reply += f"- {business_name}"

    if business_phone:
        reply += f"\n{business_phone}"

    return reply


def send_reply(email_data, reply_text, from_email=None):
    """
    Send reply via Gmail API on the original thread

    Args:
        email_data: Original email data dict containing:
            - id: Email ID
            - thread_id: Thread ID for threading
            - from: Sender email/name
            - subject: Original subject
        reply_text: Generated reply text
        from_email: Email address to send from (defaults to Config.GMAIL_USER_EMAIL)

    Returns:
        dict: Sent message data or None if failed
    """
    from gmail_listener import get_service, mark_as_read
    import base64
    from email.mime.text import MIMEText

    if from_email is None:
        from_email = Config.GMAIL_USER_EMAIL

    service = get_service()

    try:
        # Extract recipient from original sender
        original_from = email_data.get('from', '')

        # Parse email from "Name <email@example.com>" format
        import re
        email_match = re.search(r'<(.+?)>', original_from)
        if email_match:
            to_email = email_match.group(1)
        else:
            to_email = original_from

        # Get original subject
        original_subject = email_data.get('subject', '')

        # Add "Re:" prefix if not already present
        if not original_subject.lower().startswith('re:'):
            subject = f"Re: {original_subject}"
        else:
            subject = original_subject

        # Create message
        message = MIMEText(reply_text)
        message['to'] = to_email
        message['from'] = from_email
        message['subject'] = subject

        # Add threading headers
        thread_id = email_data.get('thread_id')
        message_id = email_data.get('id')

        # Add In-Reply-To and References headers for proper threading
        if message_id:
            message['In-Reply-To'] = f'<{message_id}>'
            message['References'] = f'<{message_id}>'

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Send message with thread ID for proper threading
        send_request_body = {
            'raw': raw_message,
            'threadId': thread_id
        }

        sent_message = service.users().messages().send(
            userId='me',
            body=send_request_body
        ).execute()

        print(f"✓ Reply sent to {to_email}")
        print(f"  Subject: {subject}")
        print(f"  Message ID: {sent_message['id']}")

        # Mark original email as read
        mark_as_read(email_data['id'])

        return sent_message

    except Exception as e:
        print(f"✗ Error sending reply: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_follow_up_reply(lead, business_profile, conversation_history, customer_reply):
    """
    Generate a contextual follow-up response based on qualification sequence

    Args:
        lead: Lead record from database
        business_profile: Business information
        conversation_history: List of conversation messages
        customer_reply: Latest message from customer

    Returns:
        str: Generated follow-up reply text
    """
    client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    # Get current step and next step
    current_step = lead.get('qualification_step', 1)
    next_step = cm.determine_next_step(lead, conversation_history, customer_reply)
    step_info = cm.get_step_info(next_step)

    # Format conversation context
    conversation_context = cm.format_conversation_context(lead, conversation_history)

    # Build business context
    business_name = business_profile.get('name', 'Our Team')
    brand_voice = business_profile.get('brand_voice', 'Friendly and professional')
    business_phone = business_profile.get('phone')

    # Build the prompt based on next step
    step_prompts = {
        1: "Ask about urgency: Is this an emergency, needed soon, or are they planning ahead?",
        2: "Ask for more specific details about the problem/job they described.",
        3: "Ask for their service address/location.",
        4: "Ask them to send photos of the issue if possible (mention they can reply with photos).",
        5: "Ask what days/times typically work best for them.",
        6: "Let them know you have all the info and the contractor will reach out directly to schedule."
    }

    next_question = step_prompts.get(next_step, step_prompts[1])

    prompt = f"""You are writing a follow-up email on behalf of "{business_name}", a trade business.

BRAND VOICE:
{brand_voice}

{conversation_context}

CUSTOMER'S LATEST REPLY:
{customer_reply}

YOUR TASK:
Write a warm, conversational follow-up email that:
1. Acknowledges what they just said (be specific)
2. {next_question}
3. Keep it UNDER 75 words
4. Sound natural and friendly, not robotic
5. Match the brand voice above
6. Do NOT include a signature (we'll add that separately)

CRITICAL RULES:
- NEVER promise specific availability or commit to specific times
- NEVER say WHEN you'll respond or follow up
- Use neutral language like "we'll follow up to coordinate", "we'll be in touch to schedule"
- ALWAYS ASK for the customer's preferred times/availability FIRST
- The contractor (not the AI) confirms all appointments
- Keep it brief and conversational
- Don't apologize excessively
- Don't be overly formal

Write ONLY the email body, nothing else:"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=250,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        reply_body = message.content[0].text.strip()

        # Add signature
        signature = f"\n\n- {business_name}"
        if business_phone:
            signature += f"\n{business_phone}"

        full_reply = reply_body + signature

        return full_reply

    except Exception as e:
        print(f"✗ Error generating follow-up reply with Claude: {e}")
        # Fallback to simple template
        return generate_fallback_follow_up(lead, business_profile, next_step, customer_reply)


def generate_fallback_follow_up(lead, business_profile, next_step, customer_reply):
    """
    Fallback template-based follow-up if Claude API fails

    Args:
        lead: Lead record
        business_profile: Business profile
        next_step: Next qualification step number
        customer_reply: Customer's message

    Returns:
        str: Template-based follow-up reply
    """
    business_name = business_profile.get('name', 'Our Team')
    business_phone = business_profile.get('phone')
    customer_name = lead.get('customer_name', 'there')

    # Simple acknowledgment + next question templates
    templates = {
        1: f"Thanks for getting back to us! Quick question - is this something urgent that needs immediate attention, or are you planning ahead?",
        2: f"Got it, thanks! Can you give me a bit more detail about what's going on?",
        3: f"Perfect. What's the service address where you need this done?",
        4: f"Thanks! If you can, send over a photo or two of the issue - that really helps us understand what we're dealing with.",
        5: f"Sounds good! What days or times typically work best for you? Just let us know your general availability and we'll coordinate from there.",
        6: f"Perfect, I've got everything we need. The contractor will reach out to you directly to confirm the schedule. Talk soon!"
    }

    reply = f"Hi {customer_name}!\n\n"
    reply += templates.get(next_step, templates[1])
    reply += f"\n\n- {business_name}"

    if business_phone:
        reply += f"\n{business_phone}"

    return reply
