"""Prompt templates for outreach email generation."""

OUTREACH_SYSTEM = (
    "You write short, direct, professional contractor-to-contractor outreach "
    "emails for a licensed NYC construction company. Your emails are honest, "
    "specific, and respect the reader's time. No marketing fluff, no "
    "exclamation points, no emojis, no ALL CAPS. Reference concrete details "
    "(job numbers, addresses, scope specifics) to prove you've done your "
    "homework. Always return only the JSON the user asks for, nothing else."
)


INITIAL_EMAIL_PROMPT = """Write an initial outreach email from {contractor_name} to {contact} about the project at {project}.

Context to reference in the email:
- Project address: {project}
- Reference job filing number: {job_number}
- Scope summary: {scope_summary}
- Sanz credentials: licensed in all 5 NYC boroughs, government clients include MTA and NYS Parks
- Sender: {sender} ({sender_title})
- Attachment: bid proposal PDF will be attached

Rules:
- Tone: direct, professional, contractor-to-contractor.
- Max 150 words in the body.
- Subject line should reference the address and be under 80 characters.
- Reference the job number and at least one specific detail from the scope.
- Close with a clear next step (brief call or walkthrough).
- Do not use exclamation points or marketing clichés.

Return exactly one JSON object and nothing else:
{{
  "subject": "<subject line>",
  "body": "<email body, plain text with \\n newlines>"
}}
"""


DRIP_PROMPT = """Write a {day_label} follow-up email from {contractor_name} to {contact} about the project at {project}.

Context:
- Project address: {project}
- Reference job filing number: {job_number}
- Scope summary: {scope_summary}
- Sender: {sender}
- This is follow-up #{seq} to an initial email + proposal that did not receive a reply.

Purpose for THIS follow-up: {purpose}

Rules:
- Max 100 words.
- Tone: direct, respectful, contractor-to-contractor.
- Reference the original email briefly — do not repeat the full pitch.
- Do not use exclamation points or marketing clichés.
- No emojis.
{extra_rules}

Return exactly one JSON object and nothing else:
{{
  "subject": "<subject line>",
  "body": "<email body, plain text with \\n newlines>"
}}
"""


DRIP_STEPS = [
    {
        "day": 3,
        "day_label": "day-3",
        "seq": 1,
        "purpose": "Make sure the original email landed. Be brief and low-pressure.",
        "extra_rules": "- Keep it to 2-3 short sentences.",
    },
    {
        "day": 7,
        "day_label": "day-7",
        "seq": 2,
        "purpose": "Add value by surfacing one specific detail about the job scope that the reader might care about (e.g. the specific floor, work type, or a scheduling consideration).",
        "extra_rules": "- Include at least one concrete detail pulled from the scope_summary.",
    },
    {
        "day": 14,
        "day_label": "day-14",
        "seq": 3,
        "purpose": "Create mild urgency by mentioning availability is filling up for the relevant quarter. Still respectful — not pushy.",
        "extra_rules": "- Mention a realistic scheduling constraint (e.g. Q3 availability).",
    },
    {
        "day": 21,
        "day_label": "day-21",
        "seq": 4,
        "purpose": "Close the loop. Let the reader know this is the last follow-up and the door is open if timing changes later.",
        "extra_rules": "- Make it clear this is the final follow-up.",
    },
]
