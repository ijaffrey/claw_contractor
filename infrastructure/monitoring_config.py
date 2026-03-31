#!/usr/bin/env python3
"""
Monitoring and Logging Configuration for Test Environment
"""

import logging
import json
import os
import time
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class MonitoringConfig:
    """Basic monitoring and logging for test environment"""
    
    def __init__(self):
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Ensure log directories exist
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        self.setup_logging()
        
    def setup_logging(self):
        """Configure structured logging"""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format=self.log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.log_dir / 'application.log'),
                logging.FileHandler(self.log_dir / 'error.log', level=logging.ERROR)
            ]
        )
        
        # Component-specific loggers
        components = ['database', 'security', 'api', 'notifications']
        for component in components:
            logger = logging.getLogger(component)
            handler = logging.FileHandler(self.log_dir / f'{component}.log')
            handler.setFormatter(logging.Formatter(self.log_format))
            logger.addHandler(handler)
        
        logging.info("Monitoring configured for test environment")
    
    def log_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Log a metric with optional tags"""
        metric_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'metric': metric_name,
            'value': value,
            'tags': tags or {}
        }
        
        metrics_logger = logging.getLogger('metrics')
        metrics_logger.info(json.dumps(metric_data))


class HealthChecker:
    """Basic health checks for test environment"""
    
    def __init__(self):
        self.monitoring = MonitoringConfig()
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run basic health checks"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # Check database file exists
        try:
            if os.path.exists('test_leads.db'):
                results['checks']['database'] = {'status': 'healthy', 'details': 'Database accessible'}
            else:
                results['checks']['database'] = {'status': 'warning', 'details': 'Database will be created'}
        except Exception as e:
            results['checks']['database'] = {'status': 'error', 'details': str(e)}
            results['overall_status'] = 'unhealthy'
        
        # Check filesystem write access
        try:
            test_file = self.monitoring.log_dir / 'health_test'
            test_file.write_text('test')
            test_file.unlink()
            results['checks']['filesystem'] = {'status': 'healthy', 'details': 'Writable'}
        except Exception as e:
            results['checks']['filesystem'] = {'status': 'error', 'details': str(e)}
            results['overall_status'] = 'unhealthy'
        
        return results


# Global instances
monitoring_config = MonitoringConfig()
health_checker = HealthChecker()