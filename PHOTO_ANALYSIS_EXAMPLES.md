# Photo Analysis Examples

These examples show what `photo_analyzer.py` would produce for each trade type based on the analysis prompts.

---

## PLUMBING EXAMPLE

**Image:** Water heater with visible manufacturer label

**Claude Vision Analysis Output:**
```
AO Smith 50-gallon natural gas water heater, approximately 8-10 years old based on
serial number format. Model appears to be GCR-50 series. Tank shows minor corrosion
around base pan but no active leaking visible. Temperature/pressure relief valve and
gas supply line visible on right side. Expansion tank mounted above unit. Label shows
40,000 BTU input rating.
```
*Word count: 59 words ✓*

**How this helps the plumber:**
- Know to bring 50-gal replacement (not 40 or 80)
- Prepare for gas unit (not electric)
- Expect standard residential install
- May need new expansion tank

---

## ROOFING EXAMPLE

**Image:** Residential roof with missing shingles after storm

**Claude Vision Analysis Output:**
```
Architectural asphalt shingles, charcoal/dark gray color. Approximately 6-8 missing
shingles visible in central area of main roof slope, exposing black underlayment.
Several adjacent shingles lifted but still attached. No visible sagging or structural
damage. Shingles show moderate granule loss and some curling at edges, suggesting
roof is 12-15 years old. Debris (small branches) visible on surface.
```
*Word count: 60 words ✓*

**How this helps the roofer:**
- Know shingle style/color for matching
- Estimate scope: ~8 shingles + inspection
- Understand it's storm damage (insurance)
- Assess overall roof age for replacement discussion

---

## ELECTRICAL EXAMPLE

**Image:** Main electrical service panel, door open

**Claude Vision Analysis Output:**
```
⚠️ FEDERAL PACIFIC STAB-LOK PANEL IDENTIFIED — known fire hazard, recommend
full replacement. 100-amp main breaker visible. Panel appears to be from 1970s based
on style. Approximately 8-10 open breaker slots available for new circuits. No visible
corrosion or scorching inside panel. Bus bars appear intact. This panel type has
documented history of breaker failures.
```
*Word count: 58 words ✓*

**How this helps the electrician:**
- Immediately know this is a replacement job (not repair)
- Prepare for 100A service upgrade conversation
- Quote appropriately for full panel replacement
- Safety discussion with homeowner

---

## GENERAL CONTRACTOR EXAMPLE

**Image:** Dated kitchen before remodel

**Claude Vision Analysis Output:**
```
Galley-style kitchen, approximately 10x12 feet. Oak-finish builder-grade cabinets
circa 1990s, laminate countertops, vinyl flooring. Standard white appliances
(appears to be 18-24" range). Single window above sink, no island. One doorway
visible. Cabinets show wear but structurally sound. Walls appear to be standard
drywall, painted white. Ceiling height looks standard 8 feet.
```
*Word count: 57 words ✓*

**How this helps the contractor:**
- Understand scope: full gut vs cosmetic refresh
- Estimate cabinet linear footage
- Note space constraints (galley layout)
- Prepare for appliance, counters, flooring discussion

---

## KEY FEATURES DEMONSTRATED

✅ **Factual, not diagnostic:**
- Plumbing: "Minor corrosion visible" (not "needs replacement")
- Roofing: "Missing shingles exposing underlayment" (not "you have a leak")

✅ **Specific brand/model identification:**
- Plumbing: "AO Smith GCR-50 series"
- Electrical: "Federal Pacific Stab-Lok"

✅ **Safety flags when warranted:**
- Electrical: "⚠️ FEDERAL PACIFIC STAB-LOK PANEL IDENTIFIED — known fire hazard"

✅ **Contractor-relevant details:**
- Measurements, materials, part numbers, age estimates
- Focuses on what helps them show up prepared

✅ **Concise format:**
- All outputs stay well under 80-word limit
- Lead with most important finding
- Summary paragraph style (not bullet points)

---

## HOW THIS APPEARS IN LEAD SUMMARY

Example lead report sent to plumber:

```
Urgency: Today - water heater not heating
Issue: No hot water since this morning, pilot light won't stay lit
Location: 4231 Crockett Street, Houston TX

📷 Photo Analysis:
AO Smith 50-gallon natural gas water heater, approximately 8-10 years old based on
serial number format. Model appears to be GCR-50 series. Tank shows minor corrosion
around base pan but no active leaking visible. Temperature/pressure relief valve and
gas supply line visible on right side. Expansion tank mounted above unit. Label shows
40,000 BTU input rating.

Availability: Home all day, can meet anytime
```

Plumber now knows:
- Likely thermocouple replacement (pilot won't stay lit)
- But unit is 8-10 years old → may recommend replacement
- If replacing: needs 50-gal gas unit in stock
- Bring expansion tank just in case
