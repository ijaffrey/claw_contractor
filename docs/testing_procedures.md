# Testing Procedures Documentation

## Overview
Comprehensive testing procedures for the Lead Management System, covering unit tests, integration tests, and end-to-end testing workflows.

## Test Execution Commands

### Unit Tests
```bash
# Run all unit tests
python3 run_basic_tests.py

# Run specific modules
python3 -m unittest test_lead_parser
python3 -m unittest test_email_sender
python3 -m unittest test_database
python3 -m unittest test_qualification_engine
python3 -m unittest test_notification_manager
```

### Integration Tests
```bash
# Run integration test suite
python3 -m unittest tests.test_handoff_workflow
python3 -m unittest tests.test_notification_service
python3 -m unittest tests.test_conversation_manager
```

### End-to-End Tests
```bash
# Run E2E workflows
python3 test_e2e.py
python3 test_main_integration.py
python3 test_final_handoff_integration.py
```

## Test Data Management

### Setup Test Environment
```bash
# Initialize test database
python3 test_db_setup.py

# Generate test data
python3 test_data/data_generator.py

# Seed contractor data
python3 seed_contractor.py
```

### Environment Configuration
```bash
# Set test environment
export ENVIRONMENT=test

# Validate configuration
python3 test_env_config.py
python3 test_environment_requirements.py
```

## Test Coverage Areas

### Core Components
- **Lead Parser**: Email parsing and data extraction
- **Database Operations**: CRUD operations and data integrity
- **Email Sender**: SMTP functionality and templates
- **Notification System**: Alert generation and delivery
- **Qualification Engine**: Lead scoring algorithms
- **Conversation Manager**: Multi-message handling

### Integration Points
- Gmail → Lead Parser → Database workflow
- Lead Qualification → Contractor Notification pipeline
- Conversation Manager → Reply Generator integration
- Database → Notification Logger coordination

## Test Result Validation

### Health Checks
```bash
# System health validation
python3 test_health_check.py

# Generate test reports
python3 report_generator.py

# View results
cat basic_test_report.json
cat test_health_report.json
```

### Log Analysis
```bash
# Monitor test logs
tail -f logs/test_system.log
tail -f logs/test_database.log
tail -f logs/test_notifications.log
```

## Manual Testing Procedures

### Gmail Integration Test
1. Send test email to configured account
2. Verify system detection within polling interval
3. Check parsing accuracy in logs
4. Confirm database storage

### Notification Flow Test
1. Create qualified lead in database
2. Trigger notification workflow
3. Verify contractor notification delivery
4. Check notification logging

### Conversation Test
1. Start email conversation with system
2. Send multiple replies with varied content
3. Verify appropriate response generation
4. Confirm conversation state tracking

## Troubleshooting

### Database Issues
```bash
# Test connectivity
python3 test_database.py

# Reset database
python3 test_db_setup.py --reset
```

### Email Service Issues
```bash
# Test Gmail connection
python3 test_gmail_listener.py

# Test email sending
python3 test_email_sender.py
```

### Environment Issues
```bash
# Validate setup
python3 test_env_config.py

# Check requirements
python3 test_environment_requirements.py
```

## Success Criteria
- All unit tests pass (100%)
- Integration tests complete without errors
- E2E workflows function as expected
- No data corruption in test database
- Performance meets benchmarks
