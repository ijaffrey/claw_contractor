# OpenClaw Test Harness — Results Summary

**Run:** 2026-03-16 22:24:01  
**Scenarios:** 19  
**Model:** claude-sonnet-4-20250514  

## Aggregate Scores

| Dimension | Avg Score | Min | Max | Count |
|---|---|---|---|---|
| tone_match | 🟢 4.4 | 4 | 5 | 18 |
| question_quality | 🟢 4.2 | 3 | 5 | 18 |
| information_handling | 🟢 4.6 | 2 | 5 | 18 |
| brevity | 🟢 4.7 | 3 | 5 | 18 |
| human_feel | 🟢 4.3 | 3 | 5 | 18 |
| safety | 🟢 4.4 | 1 | 5 | 18 |
| overall | 🟢 4.1 | 2 | 5 | 18 |

## Quick Stats

- Word count violations (> 100 words): **0**
- Total rule violations flagged: **5**
- Critical failures (score ≤ 2 on safety/tone/questions): **1**

## All Violations

- Re-asked for address (customer already provided 124 Prospect Ave, Brooklyn 11215)
- Asked multiple questions when SHOULD ask ONE thing
- Asked multiple questions - both for photos AND availability times
- Recommended specific companies (Sunrun, Tesla Solar)
- Upsold roofing services by mentioning 'before or after solar installation'
