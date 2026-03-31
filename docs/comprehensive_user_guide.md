# Lead Management System - User Guide

## Overview
Comprehensive guide for the Lead Management System that automates lead processing from Gmail to contractor notifications.

## Quick Start

### Prerequisites
- Python 3.11+, Gmail API credentials, Supabase database, Anthropic API key

### Setup
```bash
git clone <repository-url>
cd claw_contractor
python3 -m venv venv && source venv/bin/activate
pip3 install --break-system-packages -r requirements.txt
cp env.example .env  # Edit with your credentials
python3 test_db_setup.py && python3 seed_contractor.py
```

## Core Features

### Email Processing
**Start system**: `python3 main.py` (or `--dry-run` for testing)

**Process**: Gmail → Lead Parser → Database → Qualification → Response

**Troubleshooting**:
- Gmail auth fails: Check MAIL_USERNAME/MAIL_PASSWORD in .env
- Database errors: Verify SUPABASE_URL and SUPABASE_ANON_KEY
- Parsing fails: Check logs, update lead_parser.py if needed

### Lead Qualification
System automatically scores leads and triggers contractor notifications for qualified leads (score ≥ 80).

### Testing Commands
```bash
# Unit tests
python3 run_basic_tests.py
python3 test_lead_parser.py
python3 test_email_sender.py

# Integration tests  
python3 test_e2e.py
python3 test_main_integration.py

# Health checks
python3 test_health_check.py
python3 test_env_config.py
```

## System Architecture

**Components**: Gmail Listener, Lead Parser, Database Manager, Qualification Engine, Reply Generator, Contractor Notifier, Conversation Manager

**Data Flow**: Gmail → Parser → Database → Qualification → Decision → Response/Alert

## Configuration

**Required Environment Variables**:
- MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD
- SUPABASE_URL, SUPABASE_ANON_KEY  
- ANTHROPIC_API_KEY
- TEST_MODE (optional)

**Database**: PostgreSQL with tables: conversations, customers, leads, notification_log

## Monitoring

**Logs**: `lead_system.log`, `logs/test_*.log`

**Health Check**: `python3 test_health_check.py`

## Deployment

**Railway**: Set env vars, ensure Procfile exists, `git push railway main`

**Local Dev**: `python3 main.py --dry-run`

## Troubleshooting

**System won't start**: `pip3 install --break-system-packages -r requirements.txt`

**Email issues**: Generate new Gmail app password

**Database issues**: Verify Supabase credentials and connectivity

**Test failures**: Run `python3 test_basic_validation.py`

## Maintenance

**Regular**: Review logs, update dependencies, performance analysis

**Backup**: Export data with database utilities, backup .env file

**Best Practices**: Use dry-run for testing, monitor logs, secure env vars

## Support

**Self-help**: Check logs in `logs/`, run diagnostics, review config

**Escalation**: Collect logs, document steps, note config, contact dev team