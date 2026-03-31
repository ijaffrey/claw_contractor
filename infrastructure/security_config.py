#!/usr/bin/env python3
"""
Security Configuration for Test Environment
Basic security utilities and access controls
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration for test environment"""
    
    def __init__(self):
        # Basic security settings
        self.jwt_secret = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
        self.api_rate_limit = 100  # requests per 15 minutes
        self.session_timeout = 30  # minutes
        self.max_login_attempts = 5
        
        # Test environment allowed IPs
        self.allowed_ips = [
            '127.0.0.1',
            '::1',
            'localhost',
            '192.168.1.0/24',  # Local network
            '10.0.0.0/16'      # Docker networks
        ]
        
        logger.info("Security configuration initialized for test environment")
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, hash_value = stored_hash.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == hash_value
        except ValueError:
            return False
    
    def generate_api_key(self) -> str:
        """Generate secure API key for testing"""
        return f"test_api_{secrets.token_urlsafe(24)}"
    
    def sanitize_input(self, input_data: str) -> str:
        """Basic input sanitization"""
        if not input_data:
            return ""
        
        # Remove dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        sanitized = input_data
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP is allowed for test environment"""
        return ip_address in ['127.0.0.1', '::1', 'localhost'] or \
               ip_address.startswith('192.168.') or \
               ip_address.startswith('10.')
    
    def apply_security_headers(self, response) -> dict:
        """Apply basic security headers"""
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Content-Security-Policy': "default-src 'self'"
        }
        return headers


class AccessControl:
    """Basic access control for test environment"""
    
    def __init__(self):
        self.user_roles = {
            'admin': ['create', 'read', 'update', 'delete'],
            'contractor': ['read', 'update'],
            'user': ['read']
        }
        self.security = SecurityConfig()
    
    def check_permission(self, user_role: str, action: str) -> bool:
        """Check if user role has permission for action"""
        allowed_actions = self.user_roles.get(user_role, [])
        return action in allowed_actions
    
    def create_test_user(self, email: str, role: str = 'user') -> Dict[str, Any]:
        """Create test user for development"""
        password = secrets.token_urlsafe(12)
        password_hash = self.security.hash_password(password)
        
        user = {
            'id': secrets.token_urlsafe(8),
            'email': email,
            'role': role,
            'password_hash': password_hash,
            'api_key': self.security.generate_api_key(),
            'created_at': datetime.utcnow().isoformat(),
            'active': True
        }
        
        logger.info(f"Created test user: {email} with role: {role}")
        return user, password  # Return plaintext password for testing


# Global instances for test environment
security_config = SecurityConfig()
access_control = AccessControl()