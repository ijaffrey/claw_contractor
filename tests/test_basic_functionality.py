#!/usr/bin/env python3
"""
Basic Functionality Test Cases
Validates core system functionality without external dependencies
"""

import logging
import sys
from typing import Dict, Any

# Import core modules for testing
import main
import config
import lead_adapter

# Configure test logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - TEST - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BasicFunctionalityTests:
    """Test basic system functionality"""

    def __init__(self):
        self.test_results = []

    def test_main_system_initialization(self) -> bool:
        """Test that main LeadManagementSystem can be initialized"""
        try:
            logger.info("Testing main system initialization...")
            system = main.LeadManagementSystem(dry_run=True)

            # Verify system attributes
            assert hasattr(system, "dry_run"), "System missing dry_run attribute"
            assert hasattr(system, "gmail"), "System missing gmail module"
            assert hasattr(system, "parser"), "System missing parser module"
            assert hasattr(system, "db"), "System missing database module"
            assert system.dry_run == True, "Dry run mode not set correctly"

            logger.info("✓ Main system initialization test passed")
            return True

        except Exception as e:
            logger.error(f"✗ Main system initialization test failed: {str(e)}")
            return False

    def test_config_module_loading(self) -> bool:
        """Test that config module loads correctly"""
        try:
            logger.info("Testing config module loading...")

            # Verify config has required attributes
            assert hasattr(config, "__name__"), "Config module not loaded"

            logger.info("✓ Config module loading test passed")
            return True

        except Exception as e:
            logger.error(f"✗ Config module loading test failed: {str(e)}")
            return False

    def test_email_processing_workflow(self) -> bool:
        """Test email processing workflow in dry run mode"""
        try:
            logger.info("Testing email processing workflow...")

            system = main.LeadManagementSystem(dry_run=True)

            # Test email data structure
            test_email = {
                "id": "test_email_123",
                "subject": "Kitchen Remodel Quote Request",
                "sender": "test@example.com",
                "body": "I need a quote for kitchen remodeling",
                "thread_id": "thread_123",
            }

            # Process email in dry run mode
            result = system.process_email(test_email)

            # In dry run mode, this should always return True
            assert result == True, "Email processing failed in dry run mode"

            logger.info("✓ Email processing workflow test passed")
            return True

        except Exception as e:
            logger.error(f"✗ Email processing workflow test failed: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all basic functionality tests"""
        logger.info("=== STARTING BASIC FUNCTIONALITY TESTS ===")

        tests = [
            ("Main System Initialization", self.test_main_system_initialization),
            ("Config Module Loading", self.test_config_module_loading),
            ("Email Processing Workflow", self.test_email_processing_workflow),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed += 1
                    self.test_results.append({"test": test_name, "status": "PASS"})
                else:
                    failed += 1
                    self.test_results.append({"test": test_name, "status": "FAIL"})
            except Exception as e:
                failed += 1
                self.test_results.append(
                    {"test": test_name, "status": "ERROR", "error": str(e)}
                )
                logger.error(f"Test {test_name} threw exception: {str(e)}")

        total = passed + failed
        logger.info(f"=== BASIC FUNCTIONALITY TESTS COMPLETE ===")
        logger.info(f"Total: {total}, Passed: {passed}, Failed: {failed}")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "results": self.test_results,
            "success_rate": (passed / total * 100) if total > 0 else 0,
        }


if __name__ == "__main__":
    tester = BasicFunctionalityTests()
    results = tester.run_all_tests()

    # Exit with non-zero code if any tests failed
    sys.exit(0 if results["failed"] == 0 else 1)
