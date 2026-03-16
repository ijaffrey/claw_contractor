# OpenClaw Trade Assistant - Project Summary

## Overview

**OpenClaw** is an AI-powered lead qualification assistant for small trade businesses (plumbers, electricians, HVAC, general contractors). It automatically responds to customer inquiries via email, qualifies leads through a multi-message conversation sequence, and hands off qualified leads to the contractor.

**Status:** ✅ Fully functional, deployed on Railway, running 24/7

**Created:** March 2026

---

## What It Does

### Core Workflow

1. **Monitors Gmail inbox** (polls every 30 seconds)
2. **Detects new lead emails** from potential customers
3. **Parses lead information** using Claude AI
4. **Sends branded reply** matching business's voice
5. **Engages in multi-message conversation** to qualify the lead
6. **Stores everything in Supabase** (leads + full conversation history)
7. **Hands off to contractor** once qualified (step 6)

### 6-Step Qualification Sequence

The AI guides customers through a structured qualification process:

1. **Urgency** - Is this emergency, soon, or planning ahead?
2. **Job Details** - What specifically is the problem/job?
3. **Location** - What's the service address?
4. **Photos** - Can you send photos of the issue?
5. **Availability** - What times/days work for you?
6. **Ready for Contractor** - All info collected, contractor will reach out

Each step builds on the previous conversation context.

---

## Technology Stack

### Backend
- **Python 3.11+**
- **Gmail API** - Email monitoring and sending (OAuth2)
- **Supabase (PostgreSQL)** - Database for businesses, leads, conversations
- **Anthropic Claude API** - AI for parsing leads and generating contextual replies (claude-sonnet-4-20250514)

### Deployment
- **Railway** - 24/7 cloud hosting
- **GitHub** - Version control and auto-deployment

### Key Libraries
- `google-api-python-client` - Gmail integration
- `supabase` - Database client
- `anthropic` - Claude AI client
- `python-dotenv` - Environment configuration

---

## Architecture

### File Structure

```
openclaw/
├── main.py                          # Main orchestration loop
├── gmail_listener.py                # Gmail API integration
├── lead_parser.py                   # AI lead parsing
├── reply_generator.py               # AI reply generation
├── conversation_manager.py          # Qualification sequence logic
├── database.py                      # Supabase operations
├── config.py                        # Configuration management
├── onboard_business.py              # Interactive business onboarding CLI
│
├── schema.sql                       # Database schema
├── migration_add_business_fields.sql
├── migration_add_conversations.sql
│
├── requirements.txt                 # Python dependencies
├── Procfile                         # Railway worker configuration
├── runtime.txt                      # Python version
├── .env.example                     # Environment template
├── .railwayignore                   # Railway deployment exclusions
│
├── ONBOARDING_GUIDE.md             # Business onboarding documentation
├── RAILWAY_DEPLOYMENT.md           # Railway deployment guide
├── DEBUGGING_CONVERSATION_LOOP.md  # Troubleshooting guide
└── PROJECT_SUMMARY.md              # This file
```

### Database Schema

**businesses** table:
- Business profile (name, trade_type, brand_voice, contact info)
- Supports multi-business operation

**leads** table:
- Customer information (name, email, phone, location)
- Job details (job_type, description, urgency)
- Qualification tracking (qualification_step, status)
- Email metadata (thread_id, email_id)

**conversations** table:
- Full message history (customer + assistant)
- Linked to leads via lead_id
- Chronological order for context

---

## Key Features

### 1. Intelligent Lead Parsing
- Extracts customer name, email, phone from unstructured emails
- Identifies job type, urgency level, location
- Classifies lead source (HomeAdvisor, Angi, direct, etc.)
- Uses Claude AI for natural language understanding

### 2. Branded Reply Generation
- Matches business's unique brand voice
- Contextual responses based on conversation history
- **NEVER commits to specific times or availability**
- Asks qualifying questions one at a time
- Keeps replies concise (under 100 words)

### 3. Multi-Message Conversation Loop
- Detects replies by Gmail thread_id
- Loads full conversation history
- Determines next qualification step based on customer's response
- Advances through 6-step sequence intelligently
- Stores every message for context

### 4. Thread Detection & Deduplication
- Matches replies to existing conversations
- Prevents duplicate processing
- Maintains conversation continuity
- Updates qualification step after each exchange

### 5. Business Onboarding
- Interactive CLI wizard (`onboard_business.py`)
- Validates email and phone formats
- Collects brand voice description
- Supports multiple businesses
- Confirmation before saving

### 6. Railway Deployment
- Headless OAuth (no browser needed)
- Auto-refreshes expired Gmail tokens
- Environment-based configuration
- 24/7 continuous operation
- Auto-deploys from GitHub

---

## Data Flow

### New Lead Processing

```
1. Gmail email arrives
   ↓
2. poll_inbox() detects unread email
   ↓
3. Check thread_id → No existing lead found
   ↓
4. parse_lead() extracts customer info with Claude AI
   ↓
5. insert_lead() saves to Supabase
   ↓
6. insert_conversation_message() stores initial message (role: customer)
   ↓
7. generate_reply() creates branded response
   ↓
8. send_reply() sends via Gmail API
   ↓
9. insert_conversation_message() stores reply (role: assistant)
   ↓
10. update_lead_status() marks as 'contacted'
```

### Reply Processing

```
1. Gmail reply arrives (same thread_id)
   ↓
2. poll_inbox() detects unread email
   ↓
3. Check thread_id → Existing lead FOUND
   ↓
4. insert_conversation_message() stores customer reply
   ↓
5. get_conversation_history() loads all messages
   ↓
6. determine_next_step() analyzes reply + conversation
   ↓
7. generate_follow_up_reply() creates contextual response
   ↓
8. send_reply() sends via Gmail API
   ↓
9. insert_conversation_message() stores assistant reply
   ↓
10. update_qualification_step() advances if appropriate
```

---

## Configuration

### Environment Variables

**Required for all environments:**
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGci...
ANTHROPIC_API_KEY=sk-ant-api03-...
GMAIL_USER_EMAIL=your@email.com
GMAIL_CLIENT_ID=xxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-...
```

**Railway only:**
```bash
GMAIL_TOKEN_JSON={"token":"ya29...","refresh_token":"1//05Z8...","token_uri":"..."}
```

**Optional:**
```bash
POLL_INTERVAL_SECONDS=30  # Default: 30 seconds
```

---

## Deployment

### Local Development

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your credentials

# 3. Run Gmail OAuth (first time only)
python3 test_gmail_listener.py

# 4. Set up database (in Supabase SQL Editor)
# Run: schema.sql

# 5. Onboard a business
python3 onboard_business.py

# 6. Start the assistant
python3 main.py
```

### Railway Production

```bash
# 1. Generate token locally
python3 test_gmail_listener.py

# 2. Get token JSON
cat token.json | jq -c '.'

# 3. Push to GitHub
git push origin main

# 4. Deploy to Railway
# - Create project from GitHub repo
# - Add environment variables
# - Railway auto-deploys on push

# 5. Monitor logs
# Check Railway dashboard for deployment status
```

---

## Critical Implementation Details

### Gmail OAuth on Railway

**Problem:** Railway has no browser, so `flow.run_local_server()` fails.

**Solution:**
- Generate token locally with browser
- Store token JSON in GMAIL_TOKEN_JSON environment variable
- Load token from env on Railway
- Auto-refresh using refresh_token (no browser needed!)

```python
# On Railway
gmail_token_json = os.getenv('GMAIL_TOKEN_JSON')
token_data = json.loads(gmail_token_json)
creds = Credentials.from_authorized_user_info(token_data, SCOPES)

# Auto-refresh if expired
if creds.expired and creds.refresh_token:
    creds.refresh(Request())  # Silent refresh!
```

### Conversation Detection

**Problem:** How to detect if email is new lead vs reply?

**Solution:**
- Gmail assigns thread_id to every email
- Replies in same thread have same thread_id
- Store thread_id in leads table
- Look up existing lead by thread_id

```python
existing_lead = db.get_lead_by_thread_id(email_data['thread_id'])
if existing_lead:
    # This is a REPLY
    process_reply(email_data, existing_lead, business)
else:
    # This is a NEW LEAD
    process_new_lead(email_data, business)
```

### Scheduling Language Rules

**Critical:** Assistant must NEVER commit to specific times or promise when contractor will respond.

**Instead of:**
- ❌ "We can come this afternoon"
- ❌ "I'll call you in 15 minutes"
- ❌ "We'll get back to you soon"

**Use:**
- ✅ "What times work best for you? We'll follow up to coordinate."
- ✅ "Share your availability and we'll be in touch to schedule."
- ✅ "Let us know what days work for you."

This is enforced in both the AI prompts and fallback templates.

---

## Testing

### Manual Testing

```bash
# 1. Start the app
python3 main.py

# 2. Send test email to monitored inbox
# From: customer@example.com
# Subject: Need plumbing help
# Body: I have a leaky faucet in my kitchen

# 3. Check console output
# Should see lead detected, parsed, replied

# 4. Check Supabase
# Verify lead in leads table
# Verify messages in conversations table

# 5. Reply to the email
# Body: "It's urgent, can you come today?"

# 6. Check console output again
# Should see reply detected, conversation loaded

# 7. Check Supabase
# Verify qualification_step advanced
# Verify new messages in conversations table
```

### Debug Logging

Comprehensive debug logging added for troubleshooting:

```
🔍 DEBUG: Processing email
   Email ID: abc123
   Thread ID: xyz789

🔍 DEBUG: Checking for existing lead by thread_id
🔍 DEBUG (database.py): Looking up lead by thread_id: xyz789
   Found 1 leads

🔍 DEBUG: Found existing lead! This is a REPLY
   Lead ID: lead-uuid
   Customer: John Doe
   Current step: 1

🔍 DEBUG: Loaded 2 messages from conversation history
```

---

## Completed Features

### Phase 1: Core System (Steps 1-7) ✅
- [x] Gmail API integration with OAuth2
- [x] Lead parsing with Claude AI
- [x] Reply generation with brand voice
- [x] Supabase database integration
- [x] Email sending with threading
- [x] End-to-end workflow
- [x] Git commits for each step

### Phase 2: Pre-Launch Improvements ✅
- [x] Fixed scheduling language (no time commitments)
- [x] Business onboarding script
- [x] Railway deployment configuration

### Phase 3: Conversation Loop ✅
- [x] Conversations table
- [x] Thread detection
- [x] Conversation history loading
- [x] 6-step qualification sequence
- [x] Contextual follow-up generation
- [x] Step advancement logic

### Phase 4: Production Readiness ✅
- [x] Railway OAuth fix (headless operation)
- [x] Debug logging
- [x] Troubleshooting documentation
- [x] Migration scripts

---

## Known Limitations

1. **Gmail threading dependency** - If customer changes subject line drastically, Gmail may create new thread
2. **English only** - AI prompts optimized for English
3. **Single Gmail account** - Monitors one inbox (but supports multiple businesses)
4. **Polling-based** - Checks every 30 seconds (not instant push notifications)
5. **Text-only emails** - Image attachments in emails are not analyzed (though we ask customer to send photos)

---

## Future Enhancements

### Potential Improvements
- [ ] SMS integration (Twilio)
- [ ] Voice call handling (Twilio Voice)
- [ ] Calendar integration for actual scheduling
- [ ] Photo analysis with Claude Vision
- [ ] Multi-language support
- [ ] WhatsApp integration
- [ ] Dashboard UI for contractors
- [ ] Lead scoring and prioritization
- [ ] Automated follow-up reminders
- [ ] Integration with field service management software

### Infrastructure
- [ ] Switch from polling to Gmail push notifications (webhooks)
- [ ] Add Redis caching for conversation history
- [ ] Implement rate limiting
- [ ] Add error recovery and retries
- [ ] Metrics and monitoring (Sentry, Datadog)

---

## Environment Setup Summary

### Google Cloud Console
1. Create project
2. Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download credentials.json
5. Add test users (in OAuth consent screen)

### Supabase
1. Create project
2. Run schema.sql in SQL Editor
3. Copy project URL and anon key
4. (Optional) Run migrations if updating existing database

### Anthropic
1. Create account at console.anthropic.com
2. Generate API key
3. Add billing if needed

### Railway
1. Sign up with GitHub
2. Create new project from GitHub repo
3. Add environment variables
4. Monitor deployment logs

---

## Git Repository

**Location:** https://github.com/ijaffrey/claw_contractor

**Branch:** main

**Latest commits:**
- `44858b0` - docs: Update Railway deployment guide
- `299ad2a` - fix: Gmail OAuth works on Railway without browser (CRITICAL FIX)
- `197d4c2` - debug: Add comprehensive logging for conversation loop troubleshooting
- `190c791` - feat: Add multi-message conversation loop with 6-step qualification sequence
- `8f62773` - feat: Add Railway deployment support
- `2463250` - Add business onboarding script with new fields
- `d4caaef` - Fix scheduling language: remove ALL time commitments

---

## Support Documentation

### For Developers
- `RAILWAY_DEPLOYMENT.md` - Complete Railway setup guide
- `DEBUGGING_CONVERSATION_LOOP.md` - Troubleshooting guide with SQL queries
- `schema.sql` - Database schema with comments
- Code comments throughout all modules

### For Business Owners
- `ONBOARDING_GUIDE.md` - How to onboard a new business
- Sample brand voice examples
- Field descriptions and tips

---

## Contact & Credits

**Built with:** Claude Code (Anthropic)
**Developer:** Ian Jaffrey
**Co-Authored-By:** Claude <noreply@anthropic.com>

**Technologies:**
- Python 3.11+
- Gmail API (Google)
- Claude Sonnet 4 (Anthropic)
- Supabase (PostgreSQL)
- Railway (Deployment)

---

## License

Proprietary - All rights reserved

---

**Last Updated:** March 16, 2026
**Version:** 1.0.0
**Status:** Production-ready, deployed on Railway
