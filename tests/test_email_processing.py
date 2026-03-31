#!/usr/bin/env python3
"""
Email Processing Test Cases
Validates email parsing and processing functionality
"""

import logging
import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
import lead_parser
import gmail_listener
import main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - EMAIL_TEST - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailProcessingTests:
    """Test email processing functionality"""
    
    def __init__(self):
        self.test_results = []
        
    def test_lead_parser_module_loading(self) -> bool:
        """Test that lead parser module loads correctly"""
        try:
            logger.info("Testing lead parser module loading...")
            assert hasattr(lead_parser, '__name__'), "Lead parser module not loaded"
            logger.info("✓ Lead parser module loading test passed")
            return True
        except Exception as e:
            logger.error(f"✗ Lead parser module loading test failed: {str(e)}")
            return False
    
    def test_gmail_listener_module_loading(self) -> bool:
        """Test that gmail listener module loads correctly"""
        try:
            logger.info("Testing gmail listener module loading...")
            assert hasattr(gmail_listener, '__name__'), "Gmail listener module not loaded"
            logger.info("✓ Gmail listener module loading test passed")
            return True
        except Exception as e:
            logger.error(f"✗ Gmail listener module loading test failed: {str(e)}")
            return False
    
    def test_email_processing_dry_run(self) -> bool:
        """Test email processing in dry run mode"""
        try:
            logger.info("Testing email processing in dry run mode...")
            system = main.LeadManagementSystem(dry_run=True)
            
            test_email = {
                'id': 'test_email_789',
                'subject': 'Bathroom Remodel Request',
                'sender': 'homeowner@test.com',
                'body': 'I would like to get a quote for a full bathroom remodel.',
                'thread_id': 'thread_789'
            }
            
            result = system.process_email(test_email)
            assert result == True, "Email processing failed in dry run mode"
            
            logger.info("✓ Email processing dry run test passed")
            return True
        except Exception as e:
            logger.error(f"✗ Email processing dry run test failed: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all email processing tests"""
        logger.info("=== STARTING EMAIL PROCESSING TESTS ===")
        
        tests = [
            ('Lead Parser Module Loading', self.test_lead_parser_module_loading),
            ('Gmail Listener Module Loading', self.test_gmail_listener_module_loading),
            ('Email Processing Dry Run', self.test_email_processing_dry_run)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed += 1
                    self.test_results.append({'test': test_name, 'status': 'PASS'})
                else:
                    failed += 1
                    self.test_results.append({'test': test_name, 'status': 'FAIL'})
            except Exception as e:
                failed += 1
                self.test_results.append({'test': test_name, 'status': 'ERROR', 'error': str(e)})
                logger.error(f"Test {test_name} threw exception: {str(e)}")
        
        total = passed + failed
        logger.info(f"=== EMAIL PROCESSING TESTS COMPLETE ===")
        logger.info(f"Total: {total}, Passed: {passed}, Failed: {failed}")
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'results': self.test_results,
            'success_rate': (passed / total * 100) if total > 0 else 0
        }

if __name__ == '__main__':
    tester = EmailProcessingTests()
    results = tester.run_all_tests()
    sys.exit(0 if results['failed'] == 0 else 1)
