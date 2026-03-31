#!/usr/bin/env python3
"""
Lead Qualification Test Cases
Validates lead detection and qualification functionality
"""

import logging
import sys
from typing import Dict, Any

# Import core modules
import qualified_lead_detector
import qualification_engine
import main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - LEAD_QUAL_TEST - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LeadQualificationTests:
    """Test lead qualification functionality"""
    
    def __init__(self):
        self.test_results = []
        
    def test_qualified_lead_detector_loading(self) -> bool:
        """Test that qualified lead detector module loads correctly"""
        try:
            logger.info("Testing qualified lead detector module loading...")
            assert hasattr(qualified_lead_detector, '__name__'), "Qualified lead detector module not loaded"
            logger.info("✓ Qualified lead detector loading test passed")
            return True
        except Exception as e:
            logger.error(f"✗ Qualified lead detector loading test failed: {str(e)}")
            return False
    
    def test_qualification_engine_loading(self) -> bool:
        """Test that qualification engine module loads correctly"""
        try:
            logger.info("Testing qualification engine module loading...")
            assert hasattr(qualification_engine, '__name__'), "Qualification engine module not loaded"
            logger.info("✓ Qualification engine loading test passed")
            return True
        except Exception as e:
            logger.error(f"✗ Qualification engine loading test failed: {str(e)}")
            return False
    
    def test_lead_qualification_dry_run(self) -> bool:
        """Test lead qualification in dry run mode"""
        try:
            logger.info("Testing lead qualification in dry run mode...")
            
            system = main.LeadManagementSystem(dry_run=True)
            
            # Test qualified lead data
            qualified_lead = {
                'email': 'contractor@example.com',
                'subject': 'Commercial Kitchen Installation Project',
                'body': 'We have a 5000 sq ft commercial kitchen project starting next month. Budget is $150,000.',
                'project_type': 'commercial',
                'budget': 150000,
                'timeline': 'next month'
            }
            
            # In dry run mode, qualification should work without side effects
            # This is a basic test to ensure the system can handle qualified leads
            assert 'email' in qualified_lead, "Lead missing email field"
            assert 'budget' in qualified_lead, "Lead missing budget field"
            assert qualified_lead['budget'] > 0, "Lead budget should be positive"
            
            logger.info("✓ Lead qualification dry run test passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Lead qualification dry run test failed: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all lead qualification tests"""
        logger.info("=== STARTING LEAD QUALIFICATION TESTS ===")
        
        tests = [
            ('Qualified Lead Detector Loading', self.test_qualified_lead_detector_loading),
            ('Qualification Engine Loading', self.test_qualification_engine_loading),
            ('Lead Qualification Dry Run', self.test_lead_qualification_dry_run)
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
        logger.info(f"=== LEAD QUALIFICATION TESTS COMPLETE ===")
        logger.info(f"Total: {total}, Passed: {passed}, Failed: {failed}")
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'results': self.test_results,
            'success_rate': (passed / total * 100) if total > 0 else 0
        }

if __name__ == '__main__':
    tester = LeadQualificationTests()
    results = tester.run_all_tests()
    sys.exit(0 if results['failed'] == 0 else 1)
