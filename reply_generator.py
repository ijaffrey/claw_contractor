"""
Reply Generator Module
Uses Claude API to generate branded responses to leads
"""

from anthropic import Anthropic
from config import Config


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
4. Asks EXACTLY ONE qualifying question appropriate for a plumber:
   - For urgent/emergency: Ask about availability/timing (e.g., "Are you available for us to come by this afternoon?")
   - For normal requests: Ask about timing preference (e.g., "Would this week or next week work better for you?")
   - For leak repairs: Ask about severity (e.g., "Is the leak currently causing water damage, or is it a slow drip?")
   - For installations: Ask about timeline (e.g., "Do you have a preferred timeline for this installation?")
5. Keep it UNDER 100 words
6. Sound human and conversational, not robotic
7. Match the brand voice above
8. Do NOT include a signature (we'll add that separately)

IMPORTANT:
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

    # Select question based on urgency
    if urgency == 'emergency':
        question = "Are you available for us to come by within the next 2 hours?"
    elif urgency == 'urgent':
        question = "Would you be available for us to come by this afternoon or tomorrow morning?"
    else:
        question = "Would this week or next week work better for your schedule?"

    reply = f"Hi {customer_name}!\n\n"
    reply += f"Thanks for reaching out about the {job_type}. We can definitely help with that.\n\n"
    reply += f"{question}\n\n"
    reply += f"- {business_name}"

    if business_phone:
        reply += f"\n{business_phone}"

    return reply


def send_reply(email_id, reply_text):
    """
    Send reply via Gmail API on the original thread

    Args:
        email_id: Original email ID to reply to
        reply_text: Generated reply text
    """
    # TODO: Implement in Step 6
    pass
