# OpenClaw — Conversation Quality Testing Harness

## What This Is

A comprehensive testing system for evaluating and improving the quality of OpenClaw's lead qualification conversations. It simulates realistic multi-turn conversations across 4 trades, evaluates every reply using an AI judge, and produces a detailed scorecard.

## Why This Exists

The back-and-forth qualification messages need to feel human, read the room correctly, and follow strict rules (no time commitments, one question per reply, match the customer's energy). Before putting this in front of real contractors, we need to run hundreds of simulated conversations and fix every pattern that feels robotic, re-asks questions, or violates the rules.

## Files

### `test_scenarios.py` — The Scenario Library
- **20 detailed test scenarios** across plumbing, roofing, electrical, and GC
- **4 business profiles** with distinct brand voices
- Each scenario defines:
  - An initial lead email (from Angi, Thumbtack, HomeAdvisor, or direct)
  - A sequence of homeowner replies simulating the multi-turn conversation
  - **SHOULD rules**: what the AI reply should do at each step
  - **MUST NOT rules**: specific violations to catch
- Covers: emergencies, medium urgency, planning, vague inquiries, minimal info, mixed language, angry homeowners, price shoppers, wrong trade, non-leads, vendor spam, silence/follow-ups, commercial properties, multi-issue lists

### `test_harness.py` — The Test Runner
- Simulates full multi-turn conversations against the Claude API
- Uses a separate Claude call as an **AI evaluator** to score each reply on 7 dimensions:
  1. **Tone match** — does it match the brand voice AND the customer's energy?
  2. **Question quality** — did it ask the right next question?
  3. **Information handling** — did it use what the customer already said?
  4. **Brevity** — is the reply appropriately short?
  5. **Human feel** — does this read like a human wrote it?
  6. **Safety** — no time commitments, no technical advice, no clichés?
  7. **Overall** — aggregate quality score
- Flags all rule violations
- Outputs detailed markdown reports: per-conversation transcripts, aggregate scorecard, and a failures file

## How to Use

### Setup
```bash
cd openclaw_test_harness
pip install anthropic python-dotenv
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Run all scenarios
```bash
python3 test_harness.py
```

### Run specific subsets
```bash
python3 test_harness.py --trade plumbing       # Just plumbing
python3 test_harness.py --trade roofing         # Just roofing
python3 test_harness.py --urgency emergency     # All emergencies
python3 test_harness.py --scenario plumb_emergency_burst_pipe  # One specific
```

### Read results
Results land in `results/YYYY-MM-DD_HHMMSS/`:
- `summary.md` — aggregate scores + violation list
- `conversations/*.md` — full transcript + per-step evaluation
- `failures.md` — critical issues to fix

## The Iteration Loop

1. **Run the harness** → read the scorecard
2. **Identify the worst patterns** (low scores on tone, clichés, re-asking, verbosity)
3. **Edit the system prompt** in `test_harness.py` → `build_system_prompt()`
4. **Re-run** → compare scores
5. **Repeat until all scenarios score 4+/5 on every dimension**

The system prompt in `test_harness.py` is the canonical version. Once it's tuned to a quality level you're happy with, copy it into `reply_generator.py` and `conversation_manager.py` in the main OpenClaw codebase.

## Key Prompt Rules Baked Into the System Prompt

These are the rules that the current system prompt enforces. They came from the project's experience so far + the platform teardown research:

1. **Never commit to times or availability**
2. **One question per reply** — don't stack
3. **Match the customer's energy** — emergency = brief; planning = warm; terse = terse
4. **Never re-ask for information already provided**
5. **Under 100 words** (most replies should be 40-70)
6. **No customer-service clichés** — no "I understand your frustration," no "I'd be happy to help!"
7. **No technical advice** — you're a coordinator, not a licensed professional
8. **Graceful handoff** when qualification is complete
9. **Skip non-leads** (vendor emails, spam, billing questions)
10. **Redirect wrong-trade inquiries** politely

## Adding New Scenarios

Add scenarios to `test_scenarios.py`. Follow the existing format:

```python
{
    "id": "unique_id",
    "name": "Human-readable name",
    "business": "mikes_plumbing",  # key from BUSINESS_PROFILES
    "urgency": "emergency|soon|planning|unknown",
    "source": "angi|thumbtack|homeadvisor|direct|unknown",
    "initial_email": {
        "from": "customer@email.com",
        "subject": "Subject line",
        "body": "The email body text",
    },
    "conversation_flow": [
        {
            "step": 1,
            "ai_should": ["what the AI should do"],
            "ai_must_not": ["what the AI must not do"],
        },
        {
            "step": 2,
            "homeowner_reply": "What the customer says next",
            "ai_should": ["..."],
            "ai_must_not": ["..."],
        },
    ],
}
```

## Integration with Main Codebase

The system prompt in `build_system_prompt()` is designed to be a drop-in replacement for whatever prompt is currently in `reply_generator.py`. The key difference from the current implementation:

1. **Much more specific rules** about tone matching (the current prompt says "feels human" — this one says exactly what that means)
2. **Explicit anti-patterns** (the cliché list, the wrong-tone examples)
3. **Energy matching** — the biggest current gap. An emergency shouldn't get the same chatty tone as a planning inquiry.
4. **One-question-per-reply** — the current system sometimes stacks 2-3 questions

Once tuning is complete, the integration path is:
- Copy `build_system_prompt()` logic into `reply_generator.py`
- Update `conversation_manager.py` to use the same prompt for follow-up replies
- Keep `test_harness.py` as a regression test — run it before any prompt changes go live
