#!/usr/bin/env python3
"""
Test Environment Health Check
Validates that all test environment components are working correctly
"""

import sqlite3
import os
import json
import time
import logging
from test_env_config import TestConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_health_checks():
    """Run comprehensive health checks on the test environment"""
    logger.info("Running test environment health checks...")
    
    health_status = {
        'overall_status': 'HEALTHY',
        'timestamp': time.time(),
        'checks': {}
    }
    
    # Database connectivity check
    try:
        conn = sqlite3.connect(TestConfig.TEST_DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        expected_tables = ['leads', 'contractors', 'notifications', 'conversations']
        missing_tables = [t for t in expected_tables if t not in table_names]
        
        if not missing_tables:
            # Check data exists
            cursor.execute('SELECT COUNT(*) FROM leads')
            lead_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM contractors')
            contractor_count = cursor.fetchone()[0]
            
            health_status['checks']['database'] = {
                'status': 'PASSED',
                'details': f'Database accessible. Tables: {len(table_names)}, Leads: {lead_count}, Contractors: {contractor_count}'
            }
        else:
            health_status['checks']['database'] = {
                'status': 'FAILED',
                'details': f'Missing tables: {missing_tables}'
            }
            health_status['overall_status'] = 'UNHEALTHY'
        
        conn.close()
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'FAILED',
            'details': str(e)
        }
        health_status['overall_status'] = 'UNHEALTHY'
    
    # Environment variables check
    required_env_vars = ['DATABASE_URL', 'TESTING']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if not missing_vars:
        health_status['checks']['environment'] = {
            'status': 'PASSED',
            'details': 'All required environment variables set'
        }
    else:
        health_status['checks']['environment'] = {
            'status': 'FAILED',
            'details': f'Missing variables: {missing_vars}'
        }
        health_status['overall_status'] = 'UNHEALTHY'
    
    # Log files check
    log_files_exist = all(os.path.exists(log_file) for log_file in TestConfig.LOG_FILES)
    
    if log_files_exist:
        health_status['checks']['logging'] = {
            'status': 'PASSED',
            'details': f'All {len(TestConfig.LOG_FILES)} log files accessible'
        }
    else:
        health_status['checks']['logging'] = {
            'status': 'FAILED',
            'details': 'Some log files missing'
        }
        health_status['overall_status'] = 'UNHEALTHY'
    
    # Write health report
    with open('test_health_report.json', 'w') as f:
        json.dump(health_status, f, indent=2)
    
    return health_status

if __name__ == '__main__':
    health = run_health_checks()
    print(f"\nTest Environment Health: {health['overall_status']}")
    print("Detailed results:")
    for check, result in health['checks'].items():
        status_emoji = "✅" if result['status'] == 'PASSED' else "❌"
        print(f"  {status_emoji} {check.upper()}: {result['status']} - {result['details']}")
    
    if health['overall_status'] == 'HEALTHY':
        print("\n🎉 Test environment is ready for testing!")
    else:
        print("\n⚠️  Test environment has issues that need to be resolved.")
