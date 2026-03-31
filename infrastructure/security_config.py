#!/usr/bin/env python3
import os
import secrets
import hashlib
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecurityConfig:
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
    
    def sanitize_input(self, input_data: str) -> str:
        if not input_data:
            return ""
        dangerous_chars = ['<', '>', '"', "'", '&', ';']
        sanitized = input_data
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized[:500]
    
    def validate_ip(self, ip_address: str) -> bool:
        return ip_address in ['127.0.0.1', 'localhost']

class TestEnvironmentSecurity:
    @staticmethod
    def validate_environment():
        required_vars = ['DATABASE_URL', 'SECRET_KEY']
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
    
    @staticmethod
    def enforce_ssl():
        if os.getenv('ENVIRONMENT') in ['staging', 'production']:
            return {'ssl_mode': 'require'}
        return {}
    
    @staticmethod
    def sanitize_log_data(log_data: str) -> str:
        log_data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', log_data)
        log_data = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE_REDACTED]', log_data)
        return log_data

def initialize_security():
    security_config = SecurityConfig()
    test_security = TestEnvironmentSecurity()
    logger.info("Security configuration initialized for test environment")
    return {'config': security_config, 'test_security': test_security}
