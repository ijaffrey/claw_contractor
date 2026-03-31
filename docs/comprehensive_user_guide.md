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

## Detailed Testing Procedures

### Test Environment Setup

**Test Categories**:
- Unit tests: Individual component validation
- Integration tests: Component interaction testing
- Health checks: System status verification
- End-to-end tests: Full workflow validation

**Testing Pattern**: Import-only testing (no pytest execution)

**Core Test Commands**:
```bash
# Component tests
python3 test_database.py
python3 test_gmail_listener.py
python3 test_qualification_engine.py
python3 test_reply_generator.py

# Integration tests
python3 test_main_integration.py
python3 test_handoff_workflow.py
python3 test_notification_service.py

# System validation
python3 test_basic_validation.py
python3 validate_quality.py
python3 run_validation.py
```

### Environment Configuration Testing

**Configuration Validation**:
```bash
# Test environment setup
python3 test_env_config.py

# Database connectivity
python3 test_db_setup.py

# API credentials
python3 test_gmail_listener.py
python3 test_email_sender.py
```

**Test Data Management**:
```bash
# Generate test datasets
python3 test_data/data_generator.py

# Clean test environment
python3 test_data/data_cleaner.py

# Validate data integrity
python3 test_data_management_demo.py
```

## Advanced Troubleshooting

### API Integration Issues

**Anthropic API Problems**:
- Rate limiting: Monitor usage in dashboard
- API key issues: Verify key validity and permissions
- Response format errors: Check API version compatibility
- Timeout handling: Implement retry logic

**Supabase Database Issues**:
- Connection pooling: Configure for high concurrency
- Query performance: Analyze slow queries
- Schema migrations: Use proper migration scripts
- Backup and recovery: Regular automated backups

### Performance Monitoring

**System Metrics**:
```bash
# Generate performance report
python3 report_generator.py

# Validate system coverage
python3 validate_coverage.py

# Check health status
python3 test_health_check.py
```

**Log Analysis**:
```bash
# System activity logs
tail -f logs/test_system.log

# Database operation logs
tail -f logs/test_database.log

# Notification service logs
tail -f logs/test_notifications.log
```

## API Reference

### Core Module Functions

**Lead Processing**:
- `lead_parser.extract_lead_info()`: Parse email content
- `qualification_engine.score_lead()`: Evaluate lead quality
- `qualified_lead_handler.process_qualified_lead()`: Handle ready leads

**Communication**:
- `reply_generator.generate_response()`: Create AI responses
- `email_sender.send_reply()`: Send email responses
- `contractor_notifier.notify_contractor()`: Alert contractors

**Data Management**:
- `database_manager.store_lead()`: Save lead information
- `conversation_manager.track_conversation()`: Monitor interactions
- `notification_manager.log_notification()`: Record notifications

### Configuration Management

**Environment Variables**:
```bash
# Email configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Database configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key

# AI configuration
ANTHROPIC_API_KEY=your_anthropic_key

# System configuration
TEST_MODE=true
ENVIRONMENT=development
CONTRACTOR_EMAIL=contractor@example.com
```

## Deployment Guide

### Railway Platform Setup

**Deployment Steps**:
1. Connect GitHub repository to Railway
2. Configure environment variables in Railway dashboard
3. Set up custom domain (optional)
4. Configure deployment triggers
5. Monitor deployment logs

**Environment Variables Setup**:
- Copy all required variables from `.env.example`
- Ensure production-grade API keys
- Configure Railway-specific variables
- Test deployment with health checks

**Monitoring and Maintenance**:
- Set up log aggregation
- Configure alerting for failures
- Monitor resource usage
- Schedule regular health checks

### Local Development

**Development Environment**:
```bash
# Setup development environment
git clone <repository-url>
cd claw_contractor
python3 -m venv venv
source venv/bin/activate
pip3 install --break-system-packages -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with development credentials

# Initialize development database
python3 test_db_setup.py
python3 seed_contractor.py

# Run in development mode
python3 main.py --dry-run
```