"""
OpenClaw Test Harness
======================
Simulates full multi-turn conversations against the Claude API,
evaluates reply quality, and produces a detailed scorecard.

Usage:
    python3 test_harness.py                    # Run all scenarios (hardcoded replies)
    python3 test_harness.py --simulated        # Run with AI-simulated homeowner responses
    python3 test_harness.py --scenario plumb_emergency_burst_pipe  # Run one scenario
    python3 test_harness.py --scenario X --simulated  # Combine with simulated mode
    python3 test_harness.py --trade plumbing   # Run all plumbing scenarios
    python3 test_harness.py --urgency emergency # Run all emergencies

Modes:
    - Default (hardcoded): Uses pre-written homeowner replies from test_scenarios.py
    - Simulated (--simulated): AI generates homeowner replies based on persona traits
      (personality, communication_style, regional_flavor) for more dynamic testing

Output:
    results/YYYY-MM-DD_HHMMSS/
        ├── summary.md              # Overall scorecard
        ├── conversations/          # Full conversation transcripts
        │   ├── plumb_emergency_burst_pipe.md
        │   └── ...
        └── failures.md             # Issues flagged for review

Requires: ANTHROPIC_API_KEY in .env or environment
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("Install anthropic: pip install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Add parent directory to path to import production code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from reply_generator import build_system_prompt as production_build_system_prompt

    USE_PRODUCTION_PROMPT = True
except ImportError:
    print(
        "Warning: Could not import production reply_generator. Using test harness prompt."
    )
    USE_PRODUCTION_PROMPT = False

from test_scenarios import ALL_SCENARIOS, BUSINESS_PROFILES

# ─── Configuration ───
MODEL = "claude-sonnet-4-20250514"
MAX_REPLY_WORDS = 100  # Hard cap from project spec
EVALUATOR_MODEL = "claude-sonnet-4-20250514"
HOMEOWNER_SIMULATOR_MODEL = (
    "claude-3-haiku-20240307"  # Use haiku for fast, cost-effective simulation
)


def get_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY in your environment or .env file")
        sys.exit(1)
    return Anthropic(api_key=api_key)


# ─── System Prompt (this is the thing to iterate on) ───


def build_system_prompt(business):
    """
    Build system prompt - uses production version if available.
    This ensures we test the actual code that will run in production.
    """
    if USE_PRODUCTION_PROMPT:
        # Use production prompt from reply_generator.py
        return production_build_system_prompt(business)

    # Fallback to local prompt (for development/iteration)
    return build_system_prompt_local(business)


def build_system_prompt_local(business):
    """
    Local copy of system prompt for iteration/development.
    Copy changes to reply_generator.py when ready for production.
    """
    return f"""You are the AI assistant for {business['name']}, a {business['trade_type']} business owned by {business['owner_name']} in {business.get('location', business.get('service_area', 'your area'))}.

YOUR JOB: Respond to customer inquiries, qualify leads through natural conversation, and hand off to {business['owner_name']} once you have enough information.

BRAND VOICE: {business['brand_voice']}

CONVERSATION RULES — follow these exactly:

1. NEVER commit to a specific time, day, or availability. You don't know {business['owner_name']}'s schedule.
   - WRONG: "We can come this afternoon" / "Mike will call you in 15 minutes" / "We'll get back to you soon"
   - RIGHT: "What times work best for you?" / "Let us know your availability and we'll coordinate."
   Also don't validate or confirm timelines as "doable" or "plenty of time":
   - WRONG: "September's definitely doable" / "Six weeks is plenty of time"
   - RIGHT: "September — got it. What's the ideal start date?"
   You don't know {business['owner_name']}'s availability or project pipeline. Just collect the info.

2. ONE question per reply. This is the most important rule. Pick the single most useful thing to learn next and ask ONLY that.
   - WRONG: "Is it dripping constantly or just when flushed? And what's your address?"
   - WRONG: "What times work for you? Any days that don't work?"
   - RIGHT: "Is it dripping constantly or just when you turn it on?"
   Then wait for their answer before asking the next thing.

3. Read the room. Match the customer's energy and communication style:
   - Emergency + panicked → be brief, decisive, skip pleasantries
   - Emergency → Drop the full sign-off. No "Mike Rossi and the team at Mike's Plumbing" when someone has water on their floor. Just sign "— Mike" or nothing at all. Get to the point.
   - Planning + relaxed → be warm, conversational, take your time
   - Terse / minimal → keep your reply equally short. Don't write 80 words to someone who wrote 6.
   - Sophisticated / detailed → match their specificity. Don't dumb it down.

4. Never re-ask for information the customer already provided. Read their email carefully before replying.

5. Keep replies UNDER {MAX_REPLY_WORDS} words. Most replies should be 40-70 words. Emergencies can be even shorter.

6. Don't use customer-service clichés:
   - NEVER: "I understand your frustration" / "I apologize for any inconvenience" / "Thank you for reaching out"
   - NEVER: "I'd be happy to help!" / "Great question!" / "Absolutely!"
   - INSTEAD: Talk like a real person at {business['name']} would. Casual, direct, human.

7. Don't give technical advice, diagnose problems, or explain what might be wrong. You're a coordinator, not a licensed {business['trade_type']} professional.
   - NEVER: "Sounds like a GFCI issue" / "Could be a loose connection" / "That's probably a wax ring"
   - NEVER: "Drano can actually make things worse" / "That tarp is the right move"
   - NEVER explain WHY something might be happening — that's {business['owner_name']}'s job on-site
   - RIGHT: Frame as info-gathering: "{business['owner_name']} will want to know about [thing]. Can you tell me [specific detail]?"
   - RIGHT: Simple acknowledgment without diagnosis: "Got it — {business['owner_name']} will know what to look for"

8. When the customer has given you urgency, job details, location, and availability — transition to handoff:
   "{business['owner_name']} has everything needed to reach out directly and coordinate from here."
   Don't keep asking questions past this point.

9. If the inquiry is clearly not a lead (vendor email, spam, existing customer about billing), don't engage. Reply only to genuine service inquiries.

10. If the inquiry is for the wrong trade (e.g., someone asking a plumber about electrical work), politely redirect. Don't try to qualify it.

11. NEVER give pricing, estimates, or cost ranges. Not even "rough" ones. Pricing is {business['owner_name']}'s decision based on seeing the job. If someone asks for a price:
   - WRONG: "Typically runs $150-$400" / "Usually costs around..." / "Ballpark would be..."
   - RIGHT: "Hard to quote without seeing the setup — where are you located so we can take a look?"
   Redirect pricing questions to a site visit, not a number.

12. Never advise on insurance claims, coverage, or whether damage qualifies. If insurance comes up:
   - WRONG: "You're in good shape" / "Storm damage is usually covered" / "You should file a claim"
   - WRONG: "That's definitely an insurance job"
   - RIGHT: "Are you planning to go through insurance on this, or handle it directly?"
   - RIGHT: "{business['owner_name']} works with insurance companies regularly and can walk you through that on-site."
   Stay neutral. Collect the information. Don't advise.

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

Sign off as: {business['owner_name']} and the team at {business['name']}
Business phone: {business['phone']}"""


# ─── Homeowner Simulator ───


def simulate_homeowner_reply(
    client,
    scenario,
    business_profile,
    conversation_history,
    ai_last_message,
    step_number,
):
    """
    Simulate a realistic homeowner response using Claude API.

    Args:
        client: Anthropic client instance
        scenario: The test scenario dict containing homeowner_persona
        business_profile: The business profile dict
        conversation_history: List of prior messages (list of dicts with 'role' and 'content')
        ai_last_message: The AI's most recent message that homeowner is responding to
        step_number: Current conversation step number

    Returns:
        str: Simulated homeowner reply
    """
    persona = scenario.get("homeowner_persona", {})
    personality = persona.get("personality", "neutral")
    communication_style = persona.get("communication_style", "casual")
    regional_flavor = persona.get("regional_flavor", "general American")

    # Build conversation history for context
    history_text = ""
    if conversation_history:
        for msg in conversation_history:
            role_label = "HOMEOWNER" if msg["role"] == "user" else "CONTRACTOR AI"
            history_text += f"{role_label}: {msg['content']}\n\n"

    # Build the system prompt for homeowner simulation
    system_prompt = f"""You are simulating a homeowner responding to a contractor's AI assistant.

HOMEOWNER PERSONA:
- Personality: {personality}
- Communication style: {communication_style}
- Regional flavor: {regional_flavor}

SCENARIO CONTEXT:
Business: {business_profile['name']} ({business_profile['trade_type']})
Initial situation: {scenario.get('description', 'Service inquiry')}
Initial email subject: {scenario.get('initial_email', {}).get('subject', '')}

CONVERSATION SO FAR:
{history_text if history_text else "(This is the first exchange)"}

LATEST MESSAGE FROM CONTRACTOR:
{ai_last_message}

Generate a realistic homeowner reply that:
- Matches the persona's personality and communication style
- Uses appropriate regional language/phrasing if specified
- Responds naturally to what the contractor just asked
- Stays in character throughout
- Provides information that moves the conversation forward
- Feels authentic to how real homeowners communicate (including typos, informal language, etc. if appropriate to the persona)

IMPORTANT: Reply ONLY as the homeowner. Do not include any meta-commentary, explanations, or labels. Just write what the homeowner would write."""

    # Call Claude API to generate homeowner response
    response = client.messages.create(
        model=HOMEOWNER_SIMULATOR_MODEL,
        max_tokens=500,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": "Generate the homeowner's reply to the contractor's message above.",
            }
        ],
    )

    return response.content[0].text.strip()


# ─── Quality Evaluator ───

EVALUATOR_PROMPT = """You are a quality evaluator for an AI lead qualification assistant used by trade businesses (plumbers, roofers, electricians, general contractors).

You will be shown:
1. The business profile
2. The customer's message
3. The AI assistant's reply
4. A list of things the reply SHOULD do
5. A list of things the reply MUST NOT do

Evaluate the reply on these dimensions. Score each 1-5 (1=terrible, 5=perfect):

TONE_MATCH: Does the reply match the business's brand voice AND the customer's energy level?
- 5: Feels like the actual business owner wrote it. Energy perfectly calibrated to the situation.
- 3: Acceptable but generic. Could be any business.
- 1: Robotic, uses clichés, wrong energy for the situation.

QUESTION_QUALITY: Did the reply ask the right next question?
- 5: Asked the single most useful qualifying question given what's known so far. 
- 3: Asked a reasonable question but not the most valuable one.
- 1: Asked something already answered, asked multiple questions, or asked nothing when it should have.

INFORMATION_HANDLING: Did it use information the customer already provided without re-asking?
- 5: Acknowledged all provided info, built on it naturally, never re-asked.
- 3: Mostly good but missed something or redundantly confirmed.
- 1: Ignored what was provided or re-asked questions already answered.

BREVITY: Is the reply appropriately short?
- 5: Perfect length for the situation. Emergency = very short. Planning = slightly longer. Never bloated.
- 3: Acceptable length but could be tighter.
- 1: Way too long, or way too short for a situation that needed more.

HUMAN_FEEL: Does this read like a human wrote it?
- 5: Genuinely sounds like a tradesperson's message. Natural, warm, direct.
- 3: Acceptable but has "AI tells" — too polished, too structured, uses phrases no human would.
- 1: Obviously AI-generated. Bullet points, headers, "I'd be happy to help!" energy.

SAFETY: Did the reply avoid all "must not" behaviors?
- 5: Clean — no time commitments, no technical advice, no clichés, no re-asking.
- 3: One minor violation.
- 1: Major violation (committed to a time, gave technical advice, used customer-service script).

Also flag any specific violations of the SHOULD/MUST NOT rules.

Respond in this exact JSON format (no markdown, no backticks):
{
  "tone_match": <1-5>,
  "question_quality": <1-5>,
  "information_handling": <1-5>,
  "brevity": <1-5>,
  "human_feel": <1-5>,
  "safety": <1-5>,
  "overall": <1-5>,
  "violations": ["list of specific rule violations, or empty list"],
  "strengths": ["what the reply did well"],
  "suggestions": ["specific improvements"]
}"""


def evaluate_reply(
    client,
    business,
    customer_message,
    ai_reply,
    should_rules,
    must_not_rules,
    conversation_history=None,
):
    """Use Claude as an evaluator to score reply quality."""
    context = f"""BUSINESS: {business['name']} ({business['trade_type']})
BRAND VOICE: {business['brand_voice']}

"""
    if conversation_history:
        context += "CONVERSATION SO FAR:\n"
        for msg in conversation_history:
            role = "CUSTOMER" if msg["role"] == "user" else "ASSISTANT"
            context += f"{role}: {msg['content']}\n\n"

    context += f"""LATEST CUSTOMER MESSAGE: {customer_message}

AI REPLY TO EVALUATE: {ai_reply}

SHOULD: {json.dumps(should_rules)}

MUST NOT: {json.dumps(must_not_rules)}"""

    response = client.messages.create(
        model=EVALUATOR_MODEL,
        max_tokens=1000,
        system=EVALUATOR_PROMPT,
        messages=[{"role": "user", "content": context}],
    )

    text = response.content[0].text.strip()
    # Clean potential markdown fences
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "tone_match": 0,
            "question_quality": 0,
            "information_handling": 0,
            "brevity": 0,
            "human_feel": 0,
            "safety": 0,
            "overall": 0,
            "violations": [f"Evaluator returned unparseable response: {text[:200]}"],
            "strengths": [],
            "suggestions": [],
        }


# ─── Conversation Runner ───


def run_scenario(client, scenario, verbose=True, simulated=False):
    """Run a full multi-turn conversation for one scenario and evaluate each step."""
    business = BUSINESS_PROFILES[scenario["business"]]
    system_prompt = build_system_prompt(business)

    # Check for non-lead scenarios
    if "expected_behavior" in scenario and "SKIP" in scenario["expected_behavior"]:
        if verbose:
            print(f"\n  📧 [{scenario['id']}] Non-lead test: {scenario['name']}")
        # For non-leads, we still generate a reply to see if the AI correctly identifies it
        email = scenario["initial_email"]
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"From: {email['from']}\nSubject: {email['subject']}\n\n{email['body']}",
                }
            ],
        )
        reply = response.content[0].text
        word_count = len(reply.split())

        result = {
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "business": scenario["business"],
            "type": "non_lead",
            "expected": scenario["expected_behavior"],
            "ai_replied": True,
            "reply": reply,
            "word_count": word_count,
            "correctly_identified": False,  # Will be evaluated
            "steps": [],
        }

        if verbose:
            print(f"    AI replied ({word_count} words): {reply[:100]}...")

        return result

    # Normal lead scenario with conversation flow
    conversation_flow = scenario.get("conversation_flow", [])
    if not conversation_flow:
        return None

    email = scenario["initial_email"]
    messages = []
    step_results = []

    # Initial email
    initial_content = (
        f"From: {email['from']}\nSubject: {email['subject']}\n\n{email['body']}"
    )
    messages.append({"role": "user", "content": initial_content})

    if verbose:
        print(f"\n  📧 [{scenario['id']}] {scenario['name']}")
        print(f"    Customer: {email['body'][:80]}...")

    for step_def in conversation_flow:
        step_num = step_def["step"]

        # Handle follow-up silence steps
        if isinstance(step_num, str) and "silence" in step_num:
            # For silence follow-ups, we simulate the AI sending an unprompted follow-up
            follow_up_prompt = (
                f"The customer has not responded for {step_num.replace('_silence', '').replace('h', ' hours').replace('d', ' days')}. "
                f"Send a brief follow-up message. Keep it very short."
            )
            messages.append(
                {"role": "user", "content": f"[SYSTEM: {follow_up_prompt}]"}
            )

        elif step_num > 1:
            # For steps > 1, we need a homeowner reply to the previous AI message
            if simulated:
                # Generate simulated homeowner reply
                ai_last_message = messages[-1]["content"] if messages else ""
                homeowner_reply = simulate_homeowner_reply(
                    client,
                    scenario,
                    business,
                    messages[:-1] if len(messages) > 1 else [],
                    ai_last_message,
                    step_num,
                )
                if verbose:
                    print(
                        f"    Customer (step {step_num}, simulated): {homeowner_reply[:80]}..."
                    )
            else:
                # Use hardcoded reply from scenario
                if "homeowner_reply" not in step_def:
                    print(
                        f"    WARNING: No homeowner_reply defined for step {step_num} in non-simulated mode"
                    )
                    continue
                homeowner_reply = step_def["homeowner_reply"]
                if verbose:
                    print(f"    Customer (step {step_num}): {homeowner_reply[:80]}...")

            messages.append({"role": "user", "content": homeowner_reply})

        # Generate AI reply
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=system_prompt,
            messages=messages,
        )
        reply = response.content[0].text
        word_count = len(reply.split())
        messages.append({"role": "assistant", "content": reply})

        if verbose:
            over = " ⚠️ OVER LIMIT" if word_count > MAX_REPLY_WORDS else ""
            print(f"    AI (step {step_num}, {word_count}w{over}): {reply[:100]}...")

        # Evaluate this step
        should_rules = step_def.get("ai_should", [])
        must_not_rules = step_def.get("ai_must_not", [])

        evaluation = evaluate_reply(
            client,
            business,
            messages[-2]["content"],  # customer message
            reply,
            should_rules,
            must_not_rules,
            messages[:-2] if len(messages) > 2 else None,
        )

        step_results.append(
            {
                "step": step_num,
                "customer_message": messages[-2]["content"],
                "ai_reply": reply,
                "word_count": word_count,
                "over_word_limit": word_count > MAX_REPLY_WORDS,
                "evaluation": evaluation,
            }
        )

        if verbose and evaluation.get("violations"):
            for v in evaluation["violations"]:
                print(f"    ❌ {v}")

    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "business": scenario["business"],
        "urgency": scenario.get("urgency"),
        "source": scenario.get("source"),
        "type": "lead",
        "steps": step_results,
        "full_conversation": messages,
    }


# ─── Results Writer ───


def write_results(results, output_dir):
    """Write detailed results to markdown files."""
    output_dir = Path(output_dir)
    conv_dir = output_dir / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)

    # Calculate aggregate scores
    all_scores = {
        "tone_match": [],
        "question_quality": [],
        "information_handling": [],
        "brevity": [],
        "human_feel": [],
        "safety": [],
        "overall": [],
    }
    all_violations = []
    failures = []
    word_count_violations = 0

    for result in results:
        if result is None:
            continue

        # Write individual conversation transcript
        scenario_id = result["scenario_id"]
        with open(conv_dir / f"{scenario_id}.md", "w") as f:
            f.write(f"# {result['scenario_name']}\n\n")
            f.write(f"**Business:** {result['business']}  \n")
            f.write(f"**Urgency:** {result.get('urgency', 'N/A')}  \n")
            f.write(f"**Source:** {result.get('source', 'N/A')}  \n\n")

            if result["type"] == "non_lead":
                f.write(f"**Type:** Non-lead (should be skipped)\n")
                f.write(f"**Expected:** {result['expected']}\n\n")
                f.write(f"**AI Reply:** {result['reply']}\n\n")
                continue

            f.write("---\n\n")
            for step in result["steps"]:
                f.write(f"## Step {step['step']}\n\n")
                f.write(f"**Customer:** {step['customer_message']}\n\n")
                f.write(
                    f"**AI Reply ({step['word_count']} words):**\n> {step['ai_reply']}\n\n"
                )

                ev = step["evaluation"]
                if ev:
                    f.write("**Scores:**\n\n")
                    f.write(f"| Dimension | Score |\n|---|---|\n")
                    for dim in [
                        "tone_match",
                        "question_quality",
                        "information_handling",
                        "brevity",
                        "human_feel",
                        "safety",
                        "overall",
                    ]:
                        score = ev.get(dim, 0)
                        emoji = "🟢" if score >= 4 else "🟡" if score >= 3 else "🔴"
                        f.write(f"| {dim} | {emoji} {score}/5 |\n")

                    if ev.get("violations"):
                        f.write(f"\n**Violations:**\n")
                        for v in ev["violations"]:
                            f.write(f"- ❌ {v}\n")
                    if ev.get("strengths"):
                        f.write(f"\n**Strengths:**\n")
                        for s in ev["strengths"]:
                            f.write(f"- ✅ {s}\n")
                    if ev.get("suggestions"):
                        f.write(f"\n**Suggestions:**\n")
                        for s in ev["suggestions"]:
                            f.write(f"- 💡 {s}\n")

                    # Aggregate
                    for dim in all_scores:
                        if ev.get(dim, 0) > 0:
                            all_scores[dim].append(ev[dim])
                    if ev.get("violations"):
                        all_violations.extend(ev["violations"])
                        if any(
                            ev.get(d, 5) <= 2
                            for d in ["safety", "tone_match", "question_quality"]
                        ):
                            failures.append(
                                (scenario_id, step["step"], ev["violations"])
                            )

                if step.get("over_word_limit"):
                    word_count_violations += 1

                f.write("\n---\n\n")

    # Write summary
    with open(output_dir / "summary.md", "w") as f:
        f.write("# OpenClaw Test Harness — Results Summary\n\n")
        f.write(f"**Run:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Scenarios:** {len(results)}  \n")
        f.write(f"**Model:** {MODEL}  \n\n")

        f.write("## Aggregate Scores\n\n")
        f.write(
            "| Dimension | Avg Score | Min | Max | Count |\n|---|---|---|---|---|\n"
        )
        for dim, scores in all_scores.items():
            if scores:
                avg = sum(scores) / len(scores)
                emoji = "🟢" if avg >= 4 else "🟡" if avg >= 3 else "🔴"
                f.write(
                    f"| {dim} | {emoji} {avg:.1f} | {min(scores)} | {max(scores)} | {len(scores)} |\n"
                )

        f.write(f"\n## Quick Stats\n\n")
        f.write(
            f"- Word count violations (> {MAX_REPLY_WORDS} words): **{word_count_violations}**\n"
        )
        f.write(f"- Total rule violations flagged: **{len(all_violations)}**\n")
        f.write(
            f"- Critical failures (score ≤ 2 on safety/tone/questions): **{len(failures)}**\n"
        )

        if all_violations:
            f.write(f"\n## All Violations\n\n")
            for v in all_violations:
                f.write(f"- {v}\n")

    # Write failures file
    if failures:
        with open(output_dir / "failures.md", "w") as f:
            f.write("# Critical Failures — Review Required\n\n")
            for scenario_id, step, violations in failures:
                f.write(f"## {scenario_id} — Step {step}\n\n")
                for v in violations:
                    f.write(f"- ❌ {v}\n")
                f.write(
                    f"\n→ See full conversation: conversations/{scenario_id}.md\n\n"
                )

    return all_scores, all_violations, failures


# ─── Main ───


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw Conversation Quality Test Harness"
    )
    parser.add_argument("--scenario", help="Run a specific scenario by ID")
    parser.add_argument(
        "--trade", help="Run all scenarios for a trade (plumbing/roofing/electrical/gc)"
    )
    parser.add_argument("--urgency", help="Run all scenarios for an urgency level")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument(
        "--no-eval",
        action="store_true",
        help="Skip AI evaluation (faster, just generate replies)",
    )
    parser.add_argument(
        "--simulated",
        action="store_true",
        help="Use AI-simulated homeowner replies instead of hardcoded responses (enables dynamic conversation testing)",
    )
    args = parser.parse_args()

    # Filter scenarios
    scenarios = ALL_SCENARIOS
    if args.scenario:
        scenarios = [s for s in scenarios if s["id"] == args.scenario]
        if not scenarios:
            print(f"No scenario found with ID: {args.scenario}")
            print(f"Available: {[s['id'] for s in ALL_SCENARIOS]}")
            sys.exit(1)
    elif args.trade:
        trade_map = {
            "plumbing": "mikes_plumbing",
            "roofing": "summit_roofing",
            "electrical": "brightline_electric",
            "gc": "apex_construction",
        }
        biz = trade_map.get(args.trade)
        if biz:
            scenarios = [s for s in scenarios if s.get("business") == biz]
        else:
            print(
                f"Unknown trade: {args.trade}. Options: plumbing, roofing, electrical, gc"
            )
            sys.exit(1)
    elif args.urgency:
        scenarios = [s for s in scenarios if s.get("urgency") == args.urgency]

    verbose = not args.quiet

    print(f"\n{'='*60}")
    print(f"OpenClaw Test Harness")
    print(f"{'='*60}")
    print(f"Scenarios to run: {len(scenarios)}")
    print(f"Model: {MODEL}")
    print(f"Homeowner mode: {'SIMULATED (AI)' if args.simulated else 'HARDCODED'}")
    if args.simulated:
        print(f"Simulator model: {HOMEOWNER_SIMULATOR_MODEL}")
    print(f"Evaluation: {'ON' if not args.no_eval else 'OFF'}")
    print(f"{'='*60}")

    client = get_client()
    results = []

    for i, scenario in enumerate(scenarios):
        if verbose:
            print(f"\n[{i+1}/{len(scenarios)}] Running: {scenario['name']}")

        result = run_scenario(
            client, scenario, verbose=verbose, simulated=args.simulated
        )
        results.append(result)

    # Write results
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = f"results/{timestamp}"
    scores, violations, failures = write_results(results, output_dir)

    # Print summary
    print(f"\n{'='*60}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*60}")
    for dim, dim_scores in scores.items():
        if dim_scores:
            avg = sum(dim_scores) / len(dim_scores)
            bar = "█" * int(avg) + "░" * (5 - int(avg))
            print(f"  {dim:25s} {bar} {avg:.1f}/5")
    print(f"\n  Violations: {len(violations)}")
    print(f"  Critical failures: {len(failures)}")
    print(f"\n  Full results: {output_dir}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
