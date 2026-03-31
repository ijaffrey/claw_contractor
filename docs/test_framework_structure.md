# Test Framework Structure

## Overview
This document outlines the organizational structure and standards for our test framework, building on the existing import-only validation pattern.

## Current Directory Structure
```
tests/
├── test_conversation_manager.py    # Conversation flow testing
├── test_handoff_workflow.py        # Lead handoff testing
└── test_notification_service.py    # Notification system testing

test_*.py (root level)              # Individual module tests
├── test_lead_parser.py
├── test_database.py
├── test_email_sender.py
└── [50+ other test modules]
```

## Proposed Enhanced Structure
```
tests/
├── __init__.py                     # Test package initialization
├── unit/                          # Unit tests for individual components
│   ├── __init__.py
│   ├── test_lead_processing.py
│   ├── test_email_handling.py
│   └── test_database_operations.py
├── integration/                   # Integration tests for component interactions
│   ├── __init__.py
│   ├── test_end_to_end_workflow.py
│   └── test_service_integration.py
├── fixtures/                      # Test data and fixtures
│   ├── __init__.py
│   ├── sample_emails.json
│   └── test_leads.json
└── utils/                        # Test utilities and helpers
    ├── __init__.py
    ├── test_helpers.py
    └── mock_services.py
```

## Testing Approach
- **Import-only validation pattern**: Primary testing method (existing)
- **No pytest execution in CI/CD**: Maintains current approach
- **Manual test validation**: Through imports and run_basic_tests.py
- **Modular test organization**: Clear separation by test type

## File Naming Conventions
- Test files: `test_*.py`
- Test utilities: `*_utils.py` or `*_helpers.py`
- Test fixtures: `*_fixtures.py`
- Test data: `*.json` or `*.yaml`

## Test Categories
1. **Unit Tests**: Individual component testing (new organized structure)
2. **Integration Tests**: Component interaction testing (enhanced)
3. **Import Tests**: Module import validation (existing pattern)
4. **Configuration Tests**: Settings and environment validation

## Integration with Existing System
- Maintains compatibility with pytest.ini configuration
- Preserves existing test_*.py files in root directory
- Enhances organization without breaking current workflow
- Supports existing run_basic_tests.py validation approach

## Testing Standards
- Always use `python3`, never bare `python`
- Import-only validation for automated testing
- Manual execution for detailed testing
- Clear separation between test types
- Comprehensive documentation for each test module
