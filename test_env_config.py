#!/usr/bin/env python3
"""
Test Environment Configuration
Basic configuration for test environment setup
"""

import os
import logging
from pathlib import Path

# Configure logging for test environment
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestConfig:
    """Test environment configuration"""

    # Test database configuration
    TEST_DATABASE_URL = "sqlite:///test_leads.db"
    TEST_DATABASE_PATH = "test_leads.db"

    # Test environment variables
    TEST_ENV_VARS = {
        "DATABASE_URL": TEST_DATABASE_URL,
        "TESTING": "True",
        "DEBUG": "True",
        "MAIL_SUPPRESS_SEND": "True",
        "TEST_MODE": "True",
    }

    # Test data
    TEST_CONTRACTORS = [
        (
            "John Smith Plumbing",
            "john@smithplumbing.com",
            "555-0101",
            "plumbing,emergency repairs",
            1,
        ),
        (
            "ABC Electrical",
            "info@abcelectrical.com",
            "555-0102",
            "electrical,wiring",
            1,
        ),
        (
            "Perfect HVAC",
            "service@perfecthvac.com",
            "555-0103",
            "hvac,heating,cooling",
            1,
        ),
    ]

    TEST_LEADS = [
        ("Alice Johnson", "alice@example.com", "555-1001", "new", "email"),
        ("Bob Wilson", "bob@example.com", "555-1002", "contacted", "email"),
        ("Carol Davis", "carol@example.com", "555-1003", "qualified", "email"),
    ]

    # Log files
    LOG_FILES = [
        "logs/test_system.log",
        "logs/test_database.log",
        "logs/test_notifications.log",
    ]

    @classmethod
    def setup_environment_variables(cls):
        """Setup test environment variables"""
        logger.info("Setting up test environment variables...")
        for key, value in cls.TEST_ENV_VARS.items():
            os.environ[key] = value
            logger.info(f"Set {key} = {value}")
        return True

    @classmethod
    def create_log_directory(cls):
        """Create log directory and files"""
        logger.info("Setting up logging directory...")
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        for log_file in cls.LOG_FILES:
            Path(log_file).touch(exist_ok=True)
            logger.info(f"Created log file: {log_file}")
        return True
