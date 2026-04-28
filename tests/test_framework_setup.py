"""
Test Framework Setup Validation

This module validates that the test framework is properly configured
and all necessary components are available.
"""

import sys
import os
from pathlib import Path


def test_python_version():
    """Validate Python version meets requirements."""
    assert sys.version_info >= (3, 8), f"Python 3.8+ required, got {sys.version_info}"
    print(f"✓ Python version: {sys.version_info}")


def test_test_directory_structure():
    """Validate test directory structure exists."""
    test_dirs = ["tests/unit", "tests/integration", "tests/fixtures", "tests/utils"]

    for test_dir in test_dirs:
        assert Path(test_dir).exists(), f"Missing directory: {test_dir}"

    print("✓ Test directory structure validated")


def test_project_structure():
    """Validate project has required structure."""
    required_files = ["pytest.ini", "requirements.txt"]

    for req_file in required_files:
        assert Path(req_file).exists(), f"Missing required file: {req_file}"

    print("✓ Project structure validated")


def test_documentation_exists():
    """Validate test framework documentation exists."""
    doc_files = [
        "docs/test_framework_structure.md",
        "docs/coding_standards.md",
        "docs/code_review_guidelines.md",
    ]

    for doc_file in doc_files:
        assert Path(doc_file).exists(), f"Missing documentation: {doc_file}"

    print("✓ Documentation validated")


if __name__ == "__main__":
    test_python_version()
    test_test_directory_structure()
    test_project_structure()
    test_documentation_exists()
    print("\n🎉 Test framework setup validation complete!")
