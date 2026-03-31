# Setup Instructions - Lead Management System

## Prerequisites
- Python 3.11+ installed
- Git version control
- Gmail account with API access
- Supabase account
- Anthropic API access

## Initial Setup

### 1. Repository Setup
```bash
git clone <repository-url>
cd claw_contractor
```

### 2. Python Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip3 install --break-system-packages -r requirements.txt
```

### 3. Environment Configuration
```bash
cp env.example .env
# Edit .env file with your credentials
```

**Required Environment Variables:**
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 4. Database Setup
```bash
# Initialize database schema
python3 test_db_setup.py

# Seed initial data
python3 seed_contractor.py
```

### 5. Verify Installation
```bash
# Run health check
python3 test_health_check.py

# Validate configuration
python3 test_env_config.py

# Test basic functionality
python3 run_basic_tests.py
```

## API Credential Setup

### Gmail API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop application)
5. Download credentials JSON
6. Generate app password in Gmail settings
7. Add to .env file

### Supabase Database
1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Get project URL and anon key from Settings > API
4. Add to .env file
5. Run database initialization script

### Anthropic API
1. Sign up at [console.anthropic.com](https://console.anthropic.com/)
2. Generate API key
3. Add to .env file

## Development Environment

### Testing Setup
```bash
# Set test environment
export ENVIRONMENT=test
export TEST_MODE=true

# Generate test data
python3 test_data/data_generator.py

# Run test suite
python3 run_basic_tests.py
```

### Local Development
```bash
# Start system in dry-run mode
python3 main.py --dry-run

# Monitor logs
tail -f lead_system.log
tail -f logs/test_system.log
```

## Production Deployment

### Railway Platform
1. Connect Railway to your Git repository
2. Set environment variables in Railway dashboard
3. Deploy with automatic builds

**Railway Configuration:**
```bash
# Procfile
web: python3 main.py

# Environment variables (set in Railway dashboard)
MAIL_SERVER=smtp.gmail.com
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

## Verification Steps

### 1. Environment Validation
```bash
python3 test_env_config.py
```
Expected: All environment variables detected and valid

### 2. Database Connection
```bash
python3 test_database.py
```
Expected: Successful connection to Supabase

### 3. Email Configuration
```bash
python3 test_email_sender.py
```
Expected: SMTP connection successful

### 4. System Health
```bash
python3 test_health_check.py
cat test_health_report.json
```
Expected: All services report healthy status

### 5. End-to-End Test
```bash
python3 test_e2e.py
```
Expected: Full workflow completes without errors

## Troubleshooting Common Issues

### Import Errors
```bash
# Solution: Reinstall dependencies
pip3 install --break-system-packages -r requirements.txt
```

### Gmail Authentication
```bash
# Solution: Generate new app password
# 1. Enable 2FA on Gmail
# 2. Generate app-specific password
# 3. Update MAIL_PASSWORD in .env
```

### Database Connection
```bash
# Solution: Verify Supabase credentials
# 1. Check project URL and key
# 2. Ensure project is not paused
# 3. Verify network connectivity
```

### Permission Issues
```bash
# Solution: Check file permissions
chmod +x *.py
ls -la test_*.py
```

## Next Steps

After successful setup:
1. Review system architecture in docs/technical_documentation.md
2. Read user guide in docs/comprehensive_user_guide.md
3. Configure monitoring and alerting
4. Set up backup procedures
5. Deploy to production environment

## Support

If setup issues persist:
1. Check logs in logs/ directory
2. Run diagnostic commands
3. Review troubleshooting guide
4. Contact development team with error details