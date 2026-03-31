# Environment Setup Checklist

## Pre-requisites
- [ ] Python 3.8+ installed
- [ ] Git installed and configured
- [ ] Code editor (VS Code recommended)
- [ ] Internet connection for API access

## Initial Setup
- [ ] Clone repository
- [ ] Create Python virtual environment: `python3 -m venv venv`
- [ ] Activate virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
- [ ] Install dependencies: `pip3 install --break-system-packages -r requirements.txt`
- [ ] Copy environment template: `cp .env.example .env`

## Service Configuration
- [ ] Create Google Cloud Console project
- [ ] Enable Gmail API
- [ ] Generate OAuth2 credentials
- [ ] Download credentials.json file
- [ ] Create Supabase account and project
- [ ] Get Supabase URL and API key
- [ ] Create Anthropic account
- [ ] Generate Anthropic API key
- [ ] Update .env file with all credentials

## Database Setup
- [ ] Verify Supabase connection
- [ ] Create required database tables
- [ ] Test database operations
- [ ] Set up local SQLite for development (if needed)

## API Integration Testing
- [ ] Test Gmail API connection
- [ ] Verify email reading permissions
- [ ] Test email sending capability
- [ ] Test Anthropic Claude API
- [ ] Verify API rate limits and quotas

## Development Environment
- [ ] Configure code editor with Python extension
- [ ] Set up debugging configuration
- [ ] Install development tools (linting, formatting)
- [ ] Configure Git hooks (if applicable)
- [ ] Test hot reload functionality

## Security Verification
- [ ] Ensure .env is in .gitignore
- [ ] Verify no credentials in code
- [ ] Test OAuth flow
- [ ] Validate API key security
- [ ] Configure secure logging (no sensitive data)

## Final Validation
- [ ] Run health check script
- [ ] Test end-to-end email processing
- [ ] Verify logging functionality
- [ ] Test error handling
- [ ] Document any environment-specific configuration

## Production Readiness (Future)
- [ ] Set up production database
- [ ] Configure production logging
- [ ] Set up monitoring and alerting
- [ ] Plan backup and recovery
- [ ] Security audit and hardening