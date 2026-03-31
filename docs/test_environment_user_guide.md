# Test Environment User Guide

## Overview
This comprehensive guide covers setup, usage, and troubleshooting for the Lead Management System test environment. The system automates lead processing from Gmail to contractor notifications with comprehensive testing capabilities.

## Quick Start

### Prerequisites
- Python 3.11+ installed
- Gmail API credentials
- Supabase database account
- Anthropic API key for AI processing

### Initial Setup
```bash
# 1. Clone and enter directory
git clone <repository-url>
cd claw_contractor

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Install dependencies
pip3 install --break-system-packages -r requirements.txt

# 4. Configure environment
cp env.example .env
# Edit .env with your API keys and credentials

# 5. Initialize database
python3 test_db_setup.py
python3 seed_contractor.py
```

### Environment Configuration
Update `.env` file with required credentials:
```env
# Gmail Configuration
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Supabase Database
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-key

# Anthropic AI
ANTHROPIC_API_KEY=your-anthropic-key
```

## System Usage

### Starting the System
```bash
# Production mode
python3 main.py

# Test mode (no emails sent, no database writes)
python3 main.py --dry-run

# Web interface
python3 patrick_web/app.py
```

### Running Tests
```bash
# Quick health check
python3 test_health_check.py

# Basic test suite
python3 run_basic_tests.py

# Comprehensive validation
python3 run_validation.py

# Individual component tests
python3 test_database.py
python3 test_gmail_listener.py
python3 test_email_sender.py
```

### System Monitoring
```bash
# View real-time logs
tail -f logs/test_system.log

# Check recent errors
grep -i "error\|exception" logs/test_system.log

# System health report
cat test_health_report.json
```

## Test Environment Features

### Dry Run Mode
- Safe testing without sending emails or modifying database
- All operations logged but not executed
- Perfect for development and validation

### Test Data Management
- Automated test data generation: `python3 test_data/data_generator.py`
- Data cleanup utilities: `python3 test_data/data_cleaner.py`
- Version control for test datasets

### Validation Framework
- Automated quality checks
- Integration testing
- Performance monitoring
- Error reporting and analysis

## Troubleshooting

### Common Issues

#### Gmail Authentication Failed
**Symptoms:** "Authentication failed" or "Invalid credentials"

**Solutions:**
1. Verify Gmail credentials in `.env`
2. Enable 2-factor authentication and generate app password
3. Test connection: `python3 test_gmail_listener.py`

#### Database Connection Issues
**Symptoms:** "Unable to connect to database" or timeout errors

**Solutions:**
1. Verify Supabase URL and key in `.env`
2. Test connection: `python3 test_database.py`
3. Reset database if needed: `python3 test_db_setup.py --reset`

#### API Rate Limits
**Symptoms:** "Rate limit exceeded" or "Quota exceeded"

**Solutions:**
1. Check API quotas in respective consoles
2. Implement backoff strategies
3. Use dry-run mode for testing

#### Test Failures
**Symptoms:** Tests failing with import or dependency errors

**Solutions:**
1. Reinstall dependencies: `pip3 install --break-system-packages -r requirements.txt`
2. Check Python version: `python3 --version` (requires 3.11+)
3. Verify environment variables are set

### Log Analysis
```bash
# Check system logs
tail -100 logs/test_system.log

# Search for specific errors
grep -i "database\|gmail\|anthropic" logs/test_system.log

# View test results
cat basic_test_report.json
cat validation_report.json
```

### Performance Issues
- Monitor system resource usage
- Check network connectivity
- Verify API response times
- Review database query performance

## Advanced Usage

### Custom Test Scenarios
```bash
# Test specific workflows
python3 test_lead_qualification.py
python3 test_handoff_workflow.py

# Integration testing
python3 test_main_integration.py
python3 test_e2e.py
```

### Data Management
```bash
# Generate test leads
python3 test_data/data_generator.py --leads 100

# Clean test data
python3 test_data/data_cleaner.py --older-than 7days

# Export test results
python3 report_generator.py --format json
```

### Configuration Management
- Environment-specific configurations
- Feature flags for testing
- Debug mode settings
- Logging level adjustments

## Security Considerations

- Never commit `.env` files or credentials
- Use environment variables for sensitive data
- Regularly rotate API keys
- Monitor access logs
- Implement secure logging (no sensitive data in logs)

## Development Guidelines

### Code Standards
- Follow Python PEP 8 style guide
- Use type hints for all functions
- Write comprehensive docstrings
- Implement proper error handling

### Testing Standards
- Write tests for all new features
- Maintain >80% test coverage
- Use meaningful test names
- Include both positive and negative test cases

### Documentation
- Update documentation with code changes
- Include examples in docstrings
- Maintain troubleshooting guides
- Document configuration options

## Support and Resources

### Additional Documentation
- [Architecture Guide](docs/architecture.md)
- [Testing Procedures](docs/testing_procedures.md)
- [Troubleshooting Guide](docs/troubleshooting_guide.md)
- [Technology Stack](docs/technology_stack.md)

### Getting Help
1. Check existing documentation
2. Review log files for error details
3. Run health checks to identify issues
4. Consult troubleshooting guide
5. Contact development team if issues persist

## Version History
- v1.0: Initial release with core functionality
- Test environment setup and validation
- Comprehensive documentation and troubleshooting

Last updated: 2024-03-31
