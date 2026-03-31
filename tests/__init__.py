"""
Test Framework Package

This package contains all test modules organized by type:
- unit: Unit tests for individual components
- integration: Integration tests for component interactions
- fixtures: Test data and fixtures
- utils: Testing utilities and helpers

Testing follows import-only validation pattern compatible with existing
run_basic_tests.py and pytest.ini configuration.
"""

__version__ = "1.0.0"
__author__ = "Claw Contractor Team"

# Test framework metadata
FRAMEWORK_INFO = {
    "name": "Claw Contractor Test Framework",
    "version": __version__,
    "testing_approach": "import-only validation",
    "supported_test_types": ["unit", "integration", "fixtures", "utils"],
    "pytest_compatible": True,
    "validation_method": "manual_import"
}
