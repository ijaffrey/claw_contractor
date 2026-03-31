# Test Strategy for Claw Contractor Lead Management System

## Overview

This document outlines the comprehensive testing strategy for the Claw Contractor lead management system, including unit, integration, and acceptance testing approaches.

## Test Coverage Targets

- **Minimum Test Coverage**: 80%
- **Critical Path Coverage**: 95%
- **Business Logic Coverage**: 90%
- **API Endpoints Coverage**: 85%

## Testing Framework Selection

### Primary Testing Framework: pytest
- **Rationale**: Industry standard for Python, excellent plugin ecosystem
- **Features**: Fixtures, parameterized tests, markers, parallel execution
- **Installation**: `pip3 install pytest pytest-cov pytest-mock`

### Supporting Tools
- **Coverage**: pytest-cov for code coverage reporting
- **Mocking**: pytest-mock and unittest.mock for test isolation
- **HTTP Testing**: responses library for API mocking
- **Database Testing**: pytest-postgresql for isolated database tests
- **Performance Testing**: pytest-benchmark for performance regression

## Testing Levels

### 1. Unit Testing

**Scope**: Individual functions and classes in isolation

**Test Categories**:
- **Lead Processing Components**
  - `lead_parser.py` - Email parsing logic
  - `lead_adapter.py` - Data normalization
  - `qualification_engine.py` - Lead scoring algorithms
  - `reply_generator.py` - Response generation

- **Data Layer**
  - `database.py` - Database operations
  - `database_manager.py` - Data persistence
  - `conversation_schema.py` - Schema validation

- **Communication Layer**
  - `gmail_listener.py` - Email monitoring
  - `email_sender.py` - Email delivery
  - `contractor_notifier.py` - Notification dispatch

- **Business Logic**
  - `qualified_lead_detector.py` - Qualification logic
  - `conversation_manager.py` - Conversation flow
  - `workflow.py` - Process orchestration

**Unit Test Standards**:
- Each function must have positive and negative test cases
- Edge cases and error conditions must be tested
- External dependencies must be mocked
- Tests must be deterministic and fast (<100ms per test)

### 2. Integration Testing

**Scope**: Component interactions and data flow

**Test Categories**:
- **Email Processing Pipeline**
  - Gmail → Lead Parser → Database flow
  - Email → Reply Generator → Email Sender flow
  - Conversation threading and state management

- **Database Integration**
  - Lead storage and retrieval workflows
  - Conversation history tracking
  - Notification logging

- **External Service Integration**
  - Gmail API integration
  - Supabase database operations
  - Email delivery services

- **Web Service Integration**
  - Flask API endpoints
  - Handoff workflow services
  - Notification services

**Integration Test Standards**:
- Use test databases and mock external services
- Test complete workflows end-to-end
- Verify data consistency across components
- Test error handling and rollback scenarios


### 2. Integration Testing

**Scope**: Component interactions and data flow validation

**Test Categories**:
- **Workflow Integration**
  - Email → Lead Parser → Database workflow
  - Qualification Engine → Contractor Notifier workflow
  - Conversation Manager → Reply Generator workflow

- **Database Integration**
  - Schema validation and constraints
  - Transaction rollback scenarios
  - Concurrent access patterns

- **External Service Integration**
  - Gmail API authentication and rate limiting
  - Supabase connection and query performance
  - SMTP email delivery confirmation

### 3. Acceptance Testing

**Scope**: End-to-end business scenarios

**Test Scenarios**:
1. **New Lead Processing**: Complete email-to-notification flow
2. **Lead Qualification**: Multi-email conversation qualification
3. **Contractor Notification**: Qualified lead distribution
4. **Error Handling**: System resilience under failure conditions

## Test Data Management

### Test Data Strategy
- **Static Fixtures**: Predefined email samples and lead data
- **Factory Pattern**: Dynamic test data generation using Faker
- **Database Seeding**: Consistent test database state
- **Mock Services**: Isolated external service responses

### Test Environment Setup
```python
# conftest.py
@pytest.fixture(scope="session")
def test_database():
    """Isolated test database instance"""
    return create_test_db()

@pytest.fixture
def sample_email_data():
    """Sample email data for testing"""
    return {
        'id': 'test_email_123',
        'sender': 'test@example.com',
        'subject': 'Kitchen Remodel Inquiry',
        'body': 'I need help with kitchen renovation'
    }
```

## Testing Standards

### Code Coverage Requirements
- **Unit Tests**: ≥85% line coverage
- **Integration Tests**: ≥80% feature coverage
- **Critical Paths**: 100% coverage (lead processing, notifications)

### Test Organization
```
tests/
├── unit/
│   ├── test_lead_parser.py
│   ├── test_qualification_engine.py
│   └── test_reply_generator.py
├── integration/
│   ├── test_email_workflow.py
│   ├── test_database_operations.py
│   └── test_notification_pipeline.py
├── acceptance/
│   ├── test_complete_lead_flow.py
│   └── test_error_scenarios.py
└── fixtures/
    ├── email_samples.py
    └── lead_data.py
```

### Quality Gates
1. **Pre-commit**: Unit tests must pass
2. **CI Pipeline**: Full test suite execution
3. **Pre-deployment**: Integration and acceptance tests
4. **Performance**: Response time benchmarks

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip3 install --break-system-packages -r requirements.txt
          pip3 install --break-system-packages pytest pytest-cov pytest-mock
      
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Continuous Monitoring

### Test Metrics
- **Test Success Rate**: Track passing/failing trends
- **Coverage Trends**: Monitor coverage improvements
- **Execution Time**: Optimize slow tests
- **Flaky Tests**: Identify and fix unreliable tests

### Performance Benchmarks
- **Email Processing**: <2 seconds per email
- **Database Queries**: <100ms response time
- **Notification Delivery**: <5 seconds end-to-end

---

*This strategy will be reviewed monthly and updated based on system evolution.*