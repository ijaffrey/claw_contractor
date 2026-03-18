# OpenClaw 50-Scenario Simulated Test Results

**Run Date:** 2026-03-17 17:00:35  
**Model:** claude-sonnet-4-20250514  
**Mode:** Simulated (AI homeowner responses)  
**Total Scenarios:** 50  
**Total Conversation Turns:** 160  

---

## AGGREGATE SCORES ACROSS ALL 50 SCENARIOS

| Dimension | Avg Score | Status | Min | Max |
|-----------|-----------|--------|-----|-----|
| **tone_match** | 3.6/5 | 🟡 | 1 | 5 |
| **question_quality** | 3.1/5 | 🟡 | 1 | 5 |
| **information_handling** | 4.2/5 | 🟢 | 1 | 5 |
| **brevity** | 4.6/5 | 🟢 | 1 | 5 |
| **human_feel** | 3.8/5 | 🟡 | 1 | 5 |
| **safety** | 4.5/5 | 🟢 | 1 | 5 |
| **overall** | 3.6/5 | 🟡 | 1 | 5 |

**Quick Stats:**
- Word count violations (> 100 words): **0**
- Total rule violations flagged: **128**
- Critical failures (score ≤ 2 on safety/tone/questions): **54**

---

## KEY FINDINGS

### ✅ STRENGTHS
1. **Excellent brevity** (4.6/5) - Zero word count violations
2. **Strong safety** (4.5/5) - Avoided time commitments and technical advice in most cases
3. **Good information handling** (4.2/5) - Captured details without re-asking

### ⚠️  AREAS OF CONCERN
1. **question_quality: 3.1/5** - Most problematic dimension
2. **tone_match: 3.6/5** - Inconsistent emotional/personality matching
3. **human_feel: 3.8/5** - Breaking character, third-person references

---

## TOP 5 MOST COMMON VIOLATION TYPES (from 128 total)

1. **Failed to confirm appointment** (~18 occurrences)
   - Bot ended conversations with vague handoffs instead of scheduling confirmation
   - Example: "Jennifer has everything needed to reach out directly"

2. **Failed to acknowledge customer's specific questions/requests** (~15 occurrences)
   - Ignored technical questions, scheduling proposals, or specific concerns
   - Example: Customer asks about egress window code requirements → Bot asks for photos

3. **Third-person reference breaks character** (~12 occurrences)
   - Signing "Jennifer Okafor and the team" when speaking AS Jennifer
   - Referring to contractor in 3rd person ("Mike Rossi will..." signed "— Mike Rossi")

4. **Failed to ask qualifying question when needed** (~10 occurrences)
   - Ended conversations without gathering necessary information
   - Handoffs happened too early without full qualification

5. **Did not acknowledge photos/information customer provided** (~8 occurrences)
   - Customer sends photos → Bot asks next question without acknowledging receipt
   - Breaks conversational flow and feels robotic

---

## SCENARIOS WITH CRITICAL ISSUES (Score ≤ 2 on any dimension)

Based on failures.md, 54 critical failures across these scenarios:

### PLUMBING (6 scenarios with issues)
- **plumb_water_heater_not_heating** — Step 3: Doesn't feel like Jake writing personally
- **plumb_sewer_backup** — Step 2: Provided technical advice about water shutoff valve
- **plumb_outdoor_hose_frozen** — Step 3: Switched to third person, over-formalized
- **plumb_garbage_disposal_jammed** — Steps 1 & 3: Ignored budget concerns, didn't respect out-of-area
- **plumb_multiple_bathrooms_one_cold** — Steps 4-6: Identity confusion, didn't schedule
- **plumb_sump_pump_failure_storm** — Steps 3-4: No qualifying questions, tone mismatch

### ROOFING (9 scenarios with issues)
- **roof_hail_damage_insurance** — Steps 3, 4, 6: Didn't confirm appointment, no acknowledgment
- **roof_flat_roof_ponding** — Steps 3-4: Ended abruptly, no scheduling
- **roof_ice_dam_winter_emergency** — Steps 3-5: Made time commitment, broke character
- **roof_chimney_flashing_leak** — Steps 3 & 6: Too brief, breaking character
- **roof_skylight_leaking** — Steps 2-4: Didn't acknowledge urgency, poor close
- **roof_full_replacement_quote_shopping** — Steps 1 & 4: No qualifying question, no confirmation

### ELECTRICAL (8 scenarios with issues)
- **elec_medium_outlet_not_working** — Step 1: **Gave technical diagnosis (GFCI, connection issues)**
- **elec_ev_charger_panel_upgrade** — Steps 3-5: Didn't address questions, no appointment confirm
- **elec_partial_power_outage_elderly** — Step 2: Didn't help find local service
- **elec_smoke_detector_hardwiring** — Steps 4-5: No appointment confirmation, awkward correction
- **elec_ceiling_fan_diy_failed** — Steps 2 & 4: Missing empathy, didn't schedule
- **elec_gfci_bathroom_reno** — Steps 3-4: Avoided customer's Tuesday 23rd request
- **elec_outdoor_security_lighting** — Step 4: Third-person reference confusion

### GENERAL CONTRACTOR (10 scenarios with issues)
- **gc_basement_waterproofing_finish** — Steps 3-5: Abrupt, didn't match Midwest brand
- **gc_deck_replacement_materials** — Steps 4-5: Made time commitment, scheduling confusion
- **gc_bathroom_gut_reno** — Step 3: Deflected portfolio request defensively
- **gc_kitchen_island_addition** — Step 4: Third-person voice switch
- **gc_exterior_door_accessibility** — Step 4: Broke character completely
- **gc_drywall_repair_water_damage** — Steps 2-4: No scheduling, missed paint question
- **gc_attic_conversion_office** — Steps 2, 3, 5: **Ignored all technical questions repeatedly**
- **gc_multiroom_paint_trim** — Steps 4-5: Third-person confusion, robotic tone

---

