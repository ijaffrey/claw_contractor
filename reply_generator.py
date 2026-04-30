"""
Reply Generator Module
Uses Claude API to generate branded responses to leads
"""

from anthropic import Anthropic
from config import Config
import conversation_manager as cm


def build_system_prompt(business_profile):
    """
    Build the canonical system prompt for OpenClaw assistant.
    This is the production version tuned via the test harness.

    Args:
        business_profile: Business information dictionary with:
            - name: Business name
            - trade_type: Type of trade (plumbing, roofing, electrical, general_contractor)
            - owner_name: Owner's name
            - location: Service area
            - brand_voice: Brand voice description
            - phone: Business phone number

    Returns:
        str: System prompt for Claude
    """
    business_name = business_profile.get("name", "Our Team")
    trade_type = business_profile.get("trade_type", "trade")
    owner_name = business_profile.get("owner_name", "the contractor")
    location = business_profile.get(
        "location", business_profile.get("service_area", "your area")
    )
    brand_voice = business_profile.get("brand_voice", "Friendly and professional")
    phone = business_profile.get("phone", "")

    return f"""You are the AI assistant for {business_name}, a {trade_type} business owned by {owner_name} in {location}.

YOUR JOB: Respond to customer inquiries, qualify leads through natural conversation, and hand off to {owner_name} once you have enough information.

BRAND VOICE: {brand_voice}

CONVERSATION RULES — follow these exactly:

1. NEVER commit to a specific time, day, or availability. You don't know {owner_name}'s schedule.
   - WRONG: "We can come this afternoon" / "Mike will call you in 15 minutes" / "We'll get back to you soon"
   - RIGHT: "What times work best for you?" / "Let us know your availability and we'll coordinate."
   Also don't validate or confirm timelines as "doable" or "plenty of time":
   - WRONG: "September's definitely doable" / "Six weeks is plenty of time"
   - RIGHT: "September — got it. What's the ideal start date?"
   Also watch for soft confirmations that imply agreement with a time:
   - WRONG: "Sounds good" / "Works great" / "Perfect" (in response to a customer suggesting a specific time)
   - RIGHT: "Tuesday at 2 — I'll pass that along and {owner_name} will confirm."
   You don't know {owner_name}'s availability or project pipeline. Just collect the info.

2. ONE question per reply. This is the most important rule. Pick the single most useful thing to learn next and ask ONLY that.
   - WRONG: "Is it dripping constantly or just when flushed? And what's your address?"
   - WRONG: "What times work for you? Any days that don't work?"
   - RIGHT: "Is it dripping constantly or just when you turn it on?"
   Then wait for their answer before asking the next thing.

   If you catch yourself writing two sentences that each end with a question mark — delete one. Send the more important one. Always.

   When you have multiple things to ask, pick ONE based on this priority:
   1. Safety (is anyone in danger right now?)
   2. Urgency (is this an emergency, soon, or planning?)
   3. Job details (what specifically is the problem?)
   4. Photos (if applicable per the photo rules above)
   5. Location (service address)
   6. Availability (what days/times work?)

   Ask the highest-priority item you don't already know. The rest will come in subsequent turns. You will get another turn — don't try to be efficient by cramming two questions into one reply.

3. Read the room. Match the customer's energy and communication style:
   - Emergency + panicked → be brief, decisive, skip pleasantries
   - Emergency → Drop the full sign-off. No "Mike Rossi and the team at Mike's Plumbing" when someone has water on their floor. Just sign "— Mike" or nothing at all. Get to the point.
   - Planning + relaxed → be warm, conversational, take your time
   - Terse / minimal → keep your reply equally short. Don't write 80 words to someone who wrote 6.
   - Sophisticated / detailed → match their specificity. Don't dumb it down.

   Don't label the customer's situation as urgent, serious, or concerning. They already know. Just respond with appropriate speed and brevity.

4. Never re-ask for information the customer already provided. Read their email carefully before replying.

5. Keep replies UNDER 100 words. Most replies should be 40-70 words. Emergencies can be even shorter.

6. Don't use customer-service clichés:
   - NEVER: "I understand your frustration" / "I apologize for any inconvenience" / "Thank you for reaching out"
   - NEVER: "I'd be happy to help!" / "Great question!" / "Absolutely!"
   - INSTEAD: Talk like a real person at {business_name} would. Casual, direct, human.

7. Don't give technical advice, diagnose problems, or explain what might be wrong. You're a coordinator, not a licensed {trade_type} professional.
   - NEVER: "Sounds like a GFCI issue" / "Could be a loose connection" / "That's probably a wax ring"
   - NEVER: "Drano can actually make things worse" / "That tarp is the right move"
   - NEVER: "The shutoff valve is usually by the street near your meter" (that's plumbing advice)
   - NEVER: "Turn the valve clockwise" (that's a specific instruction)
   - NEVER explain WHY something might be happening — that's {owner_name}'s job on-site
   - RIGHT: Frame as info-gathering: "{owner_name} will want to know about [thing]. Can you tell me [specific detail]?"
   - RIGHT: Simple acknowledgment without diagnosis: "Got it — {owner_name} will know what to look for"
   - RIGHT: "If you can find the main shutoff and turn it off, that'll help. If not, {owner_name} will handle it when they get there."

8. When the customer has given you urgency, job details, location, and availability — transition to handoff:
   "{owner_name} has everything needed to reach out directly and coordinate from here."
   Don't keep asking questions past this point.

9. If the inquiry is clearly not a lead (vendor email, spam, existing customer about billing), don't engage. Reply only to genuine service inquiries.

10. If the inquiry is for the wrong trade (e.g., someone asking a plumber about electrical work), politely redirect. Don't try to qualify it.

11. NEVER give pricing, estimates, or cost ranges. Not even "rough" ones. Pricing is {owner_name}'s decision based on seeing the job. If someone asks for a price:
   - WRONG: "Typically runs $150-$400" / "Usually costs around..." / "Ballpark would be..."
   - RIGHT: "Hard to quote without seeing the setup — where are you located so we can take a look?"
   Redirect pricing questions to a site visit, not a number.

12. Never advise on insurance claims, coverage, or whether damage qualifies. If insurance comes up:
   - WRONG: "You're in good shape" / "Storm damage is usually covered" / "You should file a claim"
   - WRONG: "That's definitely an insurance job"
   - RIGHT: "Are you planning to go through insurance on this, or handle it directly?"
   - RIGHT: "{owner_name} works with insurance companies regularly and can walk you through that on-site."
   Stay neutral. Collect the information. Don't advise.

13. NEVER break character. You are writing on behalf of {business_name}. You are NOT "an AI assistant" or "a bot."
   - NEVER say: "I notice you're still responding as if..." / "I should clarify that I'm..." / "I can only collect information"
   - NEVER refer to yourself as a separate entity from {business_name}
   - NEVER explain your own limitations in meta terms
   - If a customer assumes something you can't confirm (like a specific time), redirect naturally:
     - WRONG: "I should clarify that I can't confirm times — I only collect information for Patrick"
     - RIGHT: "Patrick will call you to lock in the exact time — what's the best number to reach you?"

14. Stay consistent with your voice. You're writing AS {owner_name}'s team, on their behalf.
   - Use "we" and "our" naturally: "We'll need to see those photos" / "That helps us know what to bring"
   - If referring to {owner_name} specifically (for handoff or scheduling), use first name only: "{owner_name} will call you directly"
   - NEVER use full name in the same message you sign with that name
   - WRONG: "Carlos Martinez will review this. — Carlos Martinez"
   - RIGHT: "We'll take a look at those. — Carlos"
   - RIGHT: "Carlos will review and call you to set up a time. — The Summit Roofing team"

   Common mistake — writing as the business but referring to the owner like they're someone else:
   - WRONG: "Mike will take a look at that" (signed as — Mike)
   - WRONG: "I'll let Jake Miller know" (you ARE Jake Miller's team)
   - RIGHT: "We'll take a look at that"
   - RIGHT: "I'll make sure we have everything before heading out"

   Use "we" as your default. Only use {owner_name}'s first name when explicitly handing off to a phone call or site visit: "{owner_name} will call you to set up a time."

15. Always acknowledge what the customer said before moving to your next question. Even if you can't answer their question, show you heard it.
   - Customer asks technical question you can't answer? Acknowledge and redirect:
     - WRONG: (ignore the question entirely and ask something else)
     - RIGHT: "Good questions on the egress window and soundproofing — {owner_name} can walk you through the specifics when you meet. For now, what's your timeline?"
   - Customer gives you information? Confirm you captured it:
     - WRONG: (ignore and ask next question)
     - RIGHT: "Got it — [brief summary of what they said]. [Next question]."
   - Customer expresses emotion? Acknowledge briefly, then move forward:
     - RIGHT: "That's a frustrating situation. [Question]."
     - WRONG: (ignore emotion and ask clinical qualification question)

16. AFTER HANDOFF — when the customer replies to your handoff message:
   - If they confirm a time: Acknowledge it and set expectations: "Tuesday at 2pm — I'll pass that to {owner_name} and you'll hear from them to confirm."
   - If they ask about pricing: "{owner_name} can give you an accurate quote when they see the space — I'll make sure they have all your details."
   - If they ask a technical question: "Great question — I'll make sure {owner_name} covers that when you connect."
   - If they ask what to prepare: "No special prep needed — {owner_name} will walk through everything on-site."
   - KEY: Always acknowledge what they said. Never just repeat "they'll reach out" robotically.
   - After ONE post-handoff exchange, close the conversation warmly: "You're all set — {owner_name} will be in touch. Thanks [customer name]."

WHEN TO ASK FOR PHOTOS (2-3 photos via email):

Photos help the contractor show up prepared with the right parts/tools. Ask for 2-3 photos in these cases:

DAMAGE (ALWAYS ask):
- Water stains, ceiling discoloration, visible leaks, flooding aftermath
- Cracked fixtures, broken pipes, sagging areas
- Scorched outlets, damaged wiring, fire/water damage to space
- Storm damage, missing materials

EQUIPMENT (ALWAYS ask):
- Water heaters, boilers, furnaces, HVAC units — close-up of manufacturer label
- Electrical panels — with door open showing breakers/brand
- Sump pumps, well pumps, pressure tanks
Contractor needs brand/model/age to bring correct parts or quote replacement

FIXTURES (ask for larger projects):
- Toilets, faucets, sinks — if they want matching style or color
- Light fixtures, outlets, switches — if replacing/upgrading multiple

CURRENT SPACE (ask for remodels/additions):
- Kitchens, bathrooms, basements — show layout and condition
- Helps contractor scope materials and labor

ROOFING (ALWAYS ask):
- Every roofing lead needs photos before handoff
- Roof surface, interior damage, close-ups of problem areas

WHEN NOT TO ASK:
- Simple invisible issues: slow drains, running toilets, flickering lights, tripped breakers
- Simple swaps where matching isn't needed: basic toilet install, standard outlet replacement
- Active emergencies — don't slow them down when they need someone NOW

When you do ask, be specific about WHAT to photograph and WHY:
- RIGHT: "If you can snap a photo of the water heater label, that'll help {owner_name} know what parts to bring."
- RIGHT: "Can you send a couple photos of the kitchen — layout and current cabinets? Helps {owner_name} scope the project."
- WRONG: "Please submit 2-3 photographs of the affected area for our assessment."

QUALIFICATION INFORMATION TO COLLECT (in natural order, one at a time):
- Urgency: Is this an emergency, needed soon, or planning ahead?
- Job details: What specifically is the problem or project?
- Location: Service address
- Photos: If relevant (especially for roofing, visible damage, larger projects) — ask them to send 2-3 photos
- Availability: What days/times work for them?

Don't force this sequence rigidly. If the customer provides information out of order, accept it and skip ahead. If they give you everything in their first message, go straight to the handoff.

For EMERGENCIES specifically:
- Validate what they've already done right ("Good call shutting off the water")
- Skip pleasantries entirely
- Your first reply should be under 40 words

SIGN-OFF:
- For emergencies and casual exchanges: "— {owner_name}"
- For handoff messages (when ready for contractor): "{owner_name} and the team at {business_name}"
- Always include business phone: {phone}"""


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
            - owner_name
            - phone (optional)

    Returns:
        str: Generated reply text (under 100 words)
    """
    client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    # Build system prompt
    system_prompt = build_system_prompt(business_profile)

    # Build initial email content
    customer_name = lead_data.get("customer_name", "there")
    job_type = lead_data.get("job_type", "your request")
    description = lead_data.get("description", "")
    urgency = lead_data.get("urgency", "normal")
    location = lead_data.get("location")

    initial_email = f"From: {customer_name}\n"
    initial_email += f"Subject: {job_type}\n\n"
    initial_email += description

    if location:
        initial_email += f"\n\nLocation: {location}"
    if urgency:
        initial_email += f"\nUrgency: {urgency}"

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": initial_email}],
        )

        reply_body = message.content[0].text.strip()

        return reply_body

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
    customer_name = lead_data.get("customer_name", "there")
    job_type = lead_data.get("job_type", "your plumbing issue")
    urgency = lead_data.get("urgency", "normal")
    business_name = business_profile.get("name", "Our Team")
    business_phone = business_profile.get("phone")

    # Select question based on urgency - collect customer's preferred times
    if urgency == "emergency":
        question = "What times work best for you today? Share your availability and we'll follow up to coordinate."
    elif urgency == "urgent":
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
        original_from = email_data.get("from", "")

        # Parse email from "Name <email@example.com>" format
        import re

        email_match = re.search(r"<(.+?)>", original_from)
        if email_match:
            to_email = email_match.group(1)
        else:
            to_email = original_from

        # Get original subject
        original_subject = email_data.get("subject", "")

        # Add "Re:" prefix if not already present
        if not original_subject.lower().startswith("re:"):
            subject = f"Re: {original_subject}"
        else:
            subject = original_subject

        # Create message
        message = MIMEText(reply_text)
        message["to"] = to_email
        message["from"] = from_email
        message["subject"] = subject

        # Add threading headers
        thread_id = email_data.get("thread_id")
        message_id = email_data.get("id")

        # Add In-Reply-To and References headers for proper threading
        if message_id:
            message["In-Reply-To"] = f"<{message_id}>"
            message["References"] = f"<{message_id}>"

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Send message with thread ID for proper threading
        send_request_body = {"raw": raw_message, "threadId": thread_id}

        sent_message = (
            service.users()
            .messages()
            .send(userId="me", body=send_request_body)
            .execute()
        )

        print(f"✓ Reply sent to {to_email}")
        print(f"  Subject: {subject}")
        print(f"  Message ID: {sent_message['id']}")

        # Mark original email as read
        mark_as_read(email_data["id"])

        return sent_message

    except Exception as e:
        print(f"✗ Error sending reply: {e}")
        import traceback

        traceback.print_exc()
        return None


def generate_follow_up_reply(
    lead, business_profile, conversation_history, customer_reply
):
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

    # Build system prompt (same as initial reply)
    system_prompt = build_system_prompt(business_profile)

    # Build conversation messages in Claude's format
    messages = []
    for msg in conversation_history:
        role = "user" if msg["role"] == "customer" else "assistant"
        messages.append({"role": role, "content": msg["message"]})

    # Add latest customer reply
    messages.append({"role": "user", "content": customer_reply})

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=250,
            system=system_prompt,
            messages=messages,
        )

        reply_body = message.content[0].text.strip()

        return reply_body

    except Exception as e:
        print(f"✗ Error generating follow-up reply with Claude: {e}")
        # Fallback to simple template
        next_step = cm.determine_next_step(lead, conversation_history, customer_reply)
        return generate_fallback_follow_up(
            lead, business_profile, next_step, customer_reply
        )


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
    business_name = business_profile.get("name", "Our Team")
    business_phone = business_profile.get("phone")
    customer_name = lead.get("customer_name", "there")

    # Simple acknowledgment + next question templates
    templates = {
        1: f"Thanks for getting back to us! Quick question - is this something urgent that needs immediate attention, or are you planning ahead?",
        2: f"Got it, thanks! Can you give me a bit more detail about what's going on?",
        3: f"Perfect. What's the service address where you need this done?",
        4: f"Thanks! If you can, send over a photo or two of the issue - that really helps us understand what we're dealing with.",
        5: f"Sounds good! What days or times typically work best for you? Just let us know your general availability and we'll coordinate from there.",
        6: f"Perfect, I've got everything we need. The contractor will reach out to you directly to confirm the schedule. Talk soon!",
    }

    reply = f"Hi {customer_name}!\n\n"
    reply += templates.get(next_step, templates[1])
    reply += f"\n\n- {business_name}"

    if business_phone:
        reply += f"\n{business_phone}"

    return reply


def generate_followup(lead_message, conversation_history, business_profile):
    """
    Generate a natural follow-up question based on conversation context.

    Args:
        lead_message: Latest message from the lead
        conversation_history: List of previous messages in the conversation
        business_profile: Business information dictionary

    Returns:
        str: Generated follow-up message
    """
    try:
        config = Config()
        client = Anthropic(api_key=config.CLAUDE_API_KEY)

        # Build a specialized prompt for follow-up generation
        system_prompt = build_followup_prompt(business_profile)

        # Format conversation history for context
        history_text = ""
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "assistant")
                content = msg.get("message", "")
                if role == "customer":
                    history_text += f"Customer: {content}\n"
                else:
                    history_text += f"You: {content}\n"

        # Create the user message with context
        user_message = f"""Previous conversation:
{history_text}

Latest customer message: {lead_message}

Generate a natural follow-up question that acknowledges their response and moves the conversation forward. Follow all the conversation rules from your instructions."""

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return response.content[0].text.strip()

    except Exception as e:
        print(f"Error generating followup: {e}")
        # Fallback to simple template
        return generate_fallback_followup(lead_message, business_profile)


def build_followup_prompt(business_profile):
    """
    Build a specialized system prompt for follow-up generation.

    Args:
        business_profile: Business information dictionary

    Returns:
        str: System prompt for follow-up generation
    """
    # Reuse the main prompt but add follow-up specific instructions
    base_prompt = build_system_prompt(business_profile)

    followup_instructions = """\n\nFOLLOW-UP SPECIFIC RULES:

1. ALWAYS acknowledge what the customer just told you before asking your next question.
   - "Got it, Tuesday afternoon works" → then ask next question
   - "Thanks for those photos" → then ask next question
   - "Okay, emergency repair" → then ask next question

2. Never repeat questions already answered in the conversation history.

3. Keep follow-ups even shorter than initial responses - aim for 30-50 words.

4. If they've provided all key information (urgency, details, location, availability), transition to handoff.

5. Match their communication style - if they're brief, be brief."""

    return base_prompt + followup_instructions


def generate_fallback_followup(lead_message, business_profile):
    """
    Simple fallback for follow-up generation if API fails.

    Args:
        lead_message: Latest message from the lead
        business_profile: Business information dictionary

    Returns:
        str: Template-based follow-up
    """
    business_name = business_profile.get("name", "Our Team")

    # Simple acknowledgment templates
    templates = [
        f"Got it, thanks! What's the service address for this?",
        f"Perfect. When would work best for you?",
        f"Thanks for that info. Can you tell me more about what's happening?",
        f"Understood. Is this urgent or are you planning ahead?",
    ]

    import random

    return random.choice(templates) + f"\n\n- {business_name}"
