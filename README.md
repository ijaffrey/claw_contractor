# OpenClaw Trade Assistant

A lead qualification assistant for small trade businesses (starting with plumbers). The assistant monitors a Gmail inbox, detects incoming leads, qualifies them with follow-up questions, collects photos, and sends the owner a structured lead summary.

## Features

- 📧 Gmail inbox monitoring with OAuth2
- 🤖 AI-powered lead qualification using Claude API
- 💬 Branded responses in your business voice
- 📊 Lead storage and tracking in Supabase
- 🔄 Automated follow-up questions
- 📸 Photo collection from customers

## Tech Stack

- Python 3.11+
- Gmail API with OAuth2
- Supabase (PostgreSQL database)
- Anthropic Claude API (claude-sonnet-4-20250514)

## Project Structure

```
openclaw/
├── main.py              # Main orchestration loop
├── gmail_listener.py    # Gmail OAuth and polling
├── lead_parser.py       # Email parsing and data extraction
├── reply_generator.py   # Claude-powered reply generation
├── database.py          # Supabase database operations
├── config.py            # Configuration loader
├── .env                 # Environment variables (not in git)
├── .env.example         # Environment variables template
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd openclaw
```

### 2. Create virtual environment

```bash
python3 -11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your credentials
```

#### Getting API Credentials

**Gmail API:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth2 credentials
5. Download credentials and add to `.env`

**Supabase:**
1. Create account at [supabase.com](https://supabase.com)
2. Create a new project
3. Get URL and anon key from project settings
4. Add to `.env`

**Anthropic Claude:**
1. Sign up at [console.anthropic.com](https://console.anthropic.com/)
2. Generate an API key
3. Add to `.env`

### 5. Run the application

```bash
python main.py
```

## Sprint 1 Goal

Build a working end-to-end loop:
- Gmail listener detects a lead
- Parses it
- Sends a branded reply with one qualifying question
- Stores the lead record in Supabase

## Development Roadmap

- [x] **Step 1**: Project setup
- [ ] **Step 2**: Gmail OAuth connection
- [ ] **Step 3**: Lead parser
- [ ] **Step 4**: Supabase schema and database layer
- [ ] **Step 5**: Branded reply generator
- [ ] **Step 6**: Send reply via Gmail
- [ ] **Step 7**: Wire everything together

## License

Proprietary - All rights reserved

## Contact

For questions or support, contact the OpenClaw team.
