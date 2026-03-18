# OpenClaw Test Harness — Results Summary

**Run:** 2026-03-17 01:16:36  
**Scenarios:** 24  
**Model:** claude-sonnet-4-20250514  

## Aggregate Scores

| Dimension | Avg Score | Min | Max | Count |
|---|---|---|---|---|
| tone_match | 🟢 4.6 | 2 | 5 | 27 |
| question_quality | 🟢 4.2 | 2 | 5 | 27 |
| information_handling | 🟢 4.6 | 1 | 5 | 27 |
| brevity | 🟢 4.9 | 4 | 5 | 27 |
| human_feel | 🟢 4.7 | 3 | 5 | 27 |
| safety | 🟢 4.4 | 1 | 5 | 27 |
| overall | 🟢 4.4 | 2 | 5 | 27 |

## Quick Stats

- Word count violations (> 100 words): **0**
- Total rule violations flagged: **9**
- Critical failures (score ≤ 2 on safety/tone/questions): **4**

## All Violations

- Asked multiple questions (photos + availability times)
- Ignored customer's direct insurance question
- Re-asked about insurance when customer already indicated they want to use State Farm
- Failed to acknowledge provided information about State Farm and roof details
- Indirectly answered timeline question by asking about their timeframe rather than explaining the process needed first
- Promise availability - 'coordinate a time to knock those out' implies commitment to do the work without assessing if it's viable for the business
- Asked multiple questions when rules specify ONE question
- Skip photo request for remodel
- Multiple questions
