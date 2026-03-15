# Business Onboarding Guide

## Quick Start

### Step 1: Run the Migration (One Time Only)

If you already have an existing `businesses` table in Supabase, run this migration to add the new fields:

1. Go to your Supabase project
2. Click "SQL Editor"
3. Copy and paste the contents of `migration_add_business_fields.sql`
4. Click "Run"

**New installations:** Skip this step. The fields are already in `schema.sql`.

### Step 2: Onboard a New Business

Run the onboarding script:

```bash
python3 onboard_business.py
```

### Sample Session

```
============================================================
🦞 OpenClaw Trade Assistant - Business Onboarding
============================================================
This wizard will help you onboard a new business.
You'll be asked a series of questions about the business.
============================================================

Checking database connection...
✓ Supabase connection successful

────────────────────────────────────────────────────────────
STEP 1: Basic Information
────────────────────────────────────────────────────────────
Business name (e.g., 'Smith's Plumbing'): Joe's Plumbing & Heating

Common trade types: plumbing, electrical, hvac, general contractor
Trade type: plumbing

Owner/Contact name: Joe Martinez

Business email: joe@joesplumbing.com

Business phone (e.g., '555-123-4567'): 617-555-9876

Service area (e.g., 'Boston Metro Area'): Greater Boston & South Shore

────────────────────────────────────────────────────────────
STEP 2: Brand Voice
────────────────────────────────────────────────────────────
Describe how this business communicates with customers.
This helps the AI match the business's personality and tone.

Examples:
  • 'Friendly, professional, and family-oriented'
  • 'Direct, efficient, and no-nonsense'
  • 'Warm, helpful, and community-focused'

Brand voice description: Honest, hardworking, and down-to-earth. We're a local family business that treats every customer like a neighbor. Quick to respond, fair pricing, and we explain everything in plain English.

============================================================
BUSINESS PROFILE SUMMARY
============================================================
Business Name:  Joe's Plumbing & Heating
Trade Type:     plumbing
Owner Name:     Joe Martinez
Email:          joe@joesplumbing.com
Phone:          617-555-9876
Service Area:   Greater Boston & South Shore

Brand Voice:
Honest, hardworking, and down-to-earth. We're a local family business that treats every customer like a neighbor. Quick to respond, fair pricing, and we explain everything in plain English.
============================================================

Is this information correct? (yes/no): yes

💾 Saving business profile to database...
✓ Business created: Joe's Plumbing & Heating (ID: abc-123...)

============================================================
✅ BUSINESS ONBOARDED SUCCESSFULLY!
============================================================
Business ID:   abc-123-xyz-456
Business Name: Joe's Plumbing & Heating
Email:         joe@joesplumbing.com
Created:       2026-03-15 09:00:00+00:00
============================================================

📋 Next Steps:
1. Configure Gmail forwarding or monitoring for this business
2. Update GMAIL_USER_EMAIL in .env if needed
3. Run 'python3 main.py' to start processing leads
4. Send a test email to verify the setup

Onboard another business? (yes/no): no

✓ Onboarding complete!
```

## Field Descriptions

### Required Fields

- **Business name**: The display name for the business (e.g., "Smith's Plumbing")
- **Trade type**: Type of trade (plumbing, electrical, hvac, general contractor, etc.)
- **Email**: Business email address (validated format)
- **Brand voice**: Description of how the business communicates with customers

### Optional Fields

- **Owner/Contact name**: Name of the owner or primary contact
- **Phone**: Business phone number (validated format, at least 10 digits)
- **Service area**: Geographic area served (e.g., "Boston Metro Area")

## Brand Voice Examples

The brand voice is critical - it determines how the AI responds to customers. Here are some examples:

### Friendly & Professional
```
"Friendly, professional, and reliable. We're a family-owned plumbing
business that treats every customer like family. We respond quickly,
explain everything clearly, and always show up on time."
```

### Direct & Efficient
```
"Straightforward, efficient, and professional. We get the job done right
the first time. No nonsense, no upselling - just honest work at fair prices."
```

### Warm & Community-Focused
```
"Warm, helpful, and deeply rooted in the community. We've been serving
local families for 25 years. Your neighbors trust us, and we'll treat
your home like our own."
```

### Budget-Friendly & Honest
```
"Honest, affordable, and transparent. We understand budgets are tight.
We'll give you straight answers, fair quotes, and quality work without
breaking the bank."
```

### Premium & Expert
```
"Professional, expert, and detail-oriented. We specialize in high-end
installations and complex repairs. Licensed, insured, and committed to
craftsmanship that lasts."
```

## Tips for Success

1. **Be specific about brand voice**: The more detail you provide, the better the AI can match the business's personality.

2. **Keep trade type consistent**: Use lowercase (plumbing, electrical, hvac) for consistency.

3. **Include service area**: This helps set customer expectations about coverage.

4. **Test the voice**: After onboarding, send a test lead and review the generated reply to ensure it matches the desired tone.

5. **Multiple businesses**: You can onboard multiple businesses and process leads for all of them. Just make sure Gmail forwarding is set up correctly.

## Multi-Business Setup

If you're managing multiple businesses:

1. Onboard each business with the script
2. Set up Gmail forwarding rules to send each business's leads to the monitored inbox
3. The system will automatically match leads to the correct business based on the forwarding address
4. Each business gets replies in their own brand voice

## Troubleshooting

### Email validation fails
- Make sure the email is in format: `name@domain.com`
- No spaces or special characters except @ . _ + -

### Phone validation fails
- Include at least 10 digits
- Format doesn't matter: 555-123-4567, (555) 123-4567, or 5551234567 all work

### Database connection fails
- Check SUPABASE_URL and SUPABASE_KEY in .env
- Make sure Supabase project is running
- Run `python3 test_database.py` to verify connection

## After Onboarding

1. **Configure Gmail**: Update GMAIL_USER_EMAIL in .env to the monitored inbox
2. **Test it**: Send yourself a test lead and watch it process
3. **Review replies**: Check that the brand voice matches expectations
4. **Go live**: Start forwarding real leads!
