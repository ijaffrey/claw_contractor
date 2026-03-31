# Test Environment Specifications
## Claw Contractor Lead Management System

**Document Information**
- **Version**: 1.0
- **Date**: March 2026
- **Status**: Draft

## Environment Configuration

### Test Framework Setup
- **Framework**: pytest 7.0+ with strict configuration
- **Coverage**: 85% minimum (as per pytest.ini)
- **Timeout**: 300s maximum per test
- **Markers**: unit, integration, e2e, slow, requires_db, requires_network, smoke

### Database Environment
- **Primary**: Supabase test instance
- **Local**: SQLite for unit tests (test_leads.db)
- **Isolation**: Clean state per test run
- **Migration**: Automated schema setup

### External Service Mocking
- **Gmail API**: Mock service for unit tests
- **Email Delivery**: SMTP test doubles
- **AI Services**: Anthropic API mocks
- **Railway**: Deployment simulation

### Infrastructure Requirements
- **Python**: 3.14+ (based on __pycache__ files)
- **Memory**: <2GB RAM allocation
- **CPU**: <50% utilization target
- **Storage**: Test data cleanup automation

### Environment Variables
- **Required**: MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD
- **Optional**: SUPABASE_URL, SUPABASE_ANON_KEY
- **Test**: Separate .env.test configuration

### Test Data Management
- **Generation**: test_data/ directory structure
- **Cleanup**: Automated teardown scripts
- **Seeds**: Consistent baseline datasets
- **Privacy**: No production data usage

### Monitoring and Reporting
- **Coverage**: HTML reports in htmlcov/
- **Logs**: Structured logging to logs/ directory
- **Metrics**: Performance baseline tracking
- **Alerts**: CI/CD failure notifications

### Success Criteria
- **Execution Time**: <5 minutes total
- **Stability**: <1% flaky test rate
- **Isolation**: Zero cross-test dependencies
- **Reproducibility**: Consistent results across environments