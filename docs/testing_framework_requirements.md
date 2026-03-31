# Testing Framework Requirements

## Core Testing Dependencies

### Primary Framework
```txt
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-asyncio>=0.21.0
pytest-xdist>=3.0.0  # Parallel test execution
```

### Test Utilities
```txt
factory-boy>=3.2.0  # Test data factories
faker>=18.0.0       # Fake data generation
responses>=0.23.0   # HTTP request mocking
freezegun>=1.2.0    # Time mocking
```

### Database Testing
```txt
pytest-postgresql>=4.1.0
testcontainers>=3.7.0
```

### Performance Testing
```txt
pytest-benchmark>=4.0.0
pytest-timeout>=2.1.0
```

## Test Configuration

### pytest.ini
```ini
[tool:pytest]
minversion = 7.0
addopts = 
    --strict-markers
    --strict-config
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
    --timeout=300
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Tests that take more than 1 second
    requires_db: Tests that require database
    requires_network: Tests that require network access
    smoke: Quick smoke tests
```

### Test Directory Structure
```
tests/
├── unit/
│   ├── test_lead_parser.py
│   ├── test_qualification_engine.py
│   ├── test_reply_generator.py
│   ├── test_database_manager.py
│   └── test_email_sender.py
├── integration/
│   ├── test_email_workflow.py
│   ├── test_database_operations.py
│   ├── test_notification_pipeline.py
│   └── test_api_endpoints.py
├── e2e/
│   ├── test_complete_lead_flow.py
│   ├── test_error_scenarios.py
│   └── test_performance.py
├── fixtures/
│   ├── email_samples.py
│   ├── lead_data.py
│   ├── database_fixtures.py
│   └── api_responses.py
├── factories/
│   ├── lead_factory.py
│   ├── email_factory.py
│   └── conversation_factory.py
└── conftest.py
```

## Test Environment Setup

### conftest.py Configuration
```python
import pytest
import tempfile
import os
from unittest.mock import patch
from datetime import datetime

# Test Database Setup
@pytest.fixture(scope="session")
def test_database():
    """Create isolated test database"""
    # Implementation depends on database choice
    pass

@pytest.fixture(autouse=True)
def clean_database(test_database):
    """Clean database between tests"""
    yield
    # Clean up database state

# Mock External Services
@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service"""
    with patch('gmail_listener.build') as mock_service:
        yield mock_service

@pytest.fixture
def mock_email_sender():
    """Mock email sending service"""
    with patch('email_sender.send_email') as mock_sender:
        mock_sender.return_value = True
        yield mock_sender

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    with patch('database.supabase') as mock_db:
        yield mock_db

# Test Data Fixtures
@pytest.fixture
def sample_email():
    """Sample email data for testing"""
    return {
        'id': 'test_email_123',
        'sender': 'customer@example.com',
        'subject': 'Kitchen Remodel Inquiry',
        'body': 'I need help with a kitchen renovation project',
        'timestamp': datetime.now().isoformat()
    }

@pytest.fixture
def sample_lead():
    """Sample lead data for testing"""
    return {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'phone': '555-0123',
        'project_type': 'kitchen_remodel',
        'budget_range': '$25k-50k',
        'timeline': '3-6 months',
        'location': 'San Francisco, CA'
    }
```

## Test Standards Compliance

### Naming Conventions
- Test files: `test_{module_name}.py`
- Test functions: `test_{function_name}_{scenario}`
- Test classes: `Test{ClassName}`
- Fixtures: `{data_type}_fixture`
- Factories: `{Model}Factory`

### Test Structure (AAA Pattern)
```python
def test_function_name():
    # Arrange - Set up test data and mocks
    input_data = sample_fixture
    expected_result = expected_output
    
    # Act - Execute the function under test
    result = function_under_test(input_data)
    
    # Assert - Verify the expected outcome
    assert result == expected_result
```

### Performance Requirements
- Unit tests: Complete in < 100ms each
- Integration tests: Complete in < 5 seconds each
- E2E tests: Complete in < 30 seconds each
- Full test suite: Complete in < 10 minutes

### Coverage Requirements
- Minimum line coverage: 85%
- Critical path coverage: 100%
- Branch coverage: 80%
- Function coverage: 90%