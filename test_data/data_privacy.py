#!/usr/bin/env python3
"""
Privacy Compliant Data Manager
Ensures test data complies with privacy regulations
"""

import json
import hashlib
import re
from typing import Dict, List, Any
import logging
from datetime import datetime

class PrivacyCompliantDataManager:
    """Manages privacy compliance for test data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b'
        }
        
        self.sensitive_fields = ['email', 'phone', 'address', 'name', 'contact_name']
    
    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive data in test records"""
        anonymized = data.copy()
        
        for field in self.sensitive_fields:
            if field in anonymized:
                anonymized[field] = self._anonymize_field(field, anonymized[field])
        
        # Handle nested data
        for key, value in anonymized.items():
            if isinstance(value, dict):
                anonymized[key] = self.anonymize_data(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                anonymized[key] = [self.anonymize_data(item) for item in value]
        
        return anonymized
    
    def _anonymize_field(self, field_name: str, value: str) -> str:
        """Anonymize a specific field based on its type"""
        if not isinstance(value, str):
            return value
        
        if field_name == 'email':
            return self._hash_preserve_domain(value)
        elif field_name == 'phone':
            return 'XXX-XXX-' + value[-4:] if len(value) >= 4 else 'XXX-XXXX'
        elif field_name in ['name', 'contact_name']:
            return self._hash_name(value)
        elif field_name == 'address':
            return re.sub(r'\d+', 'XXX', value)
        else:
            return self._generate_hash(value)[:8]
    
    def _hash_preserve_domain(self, email: str) -> str:
        """Hash email but preserve domain for testing"""
        if '@' in email:
            local, domain = email.split('@', 1)
            return f"{self._generate_hash(local)[:8]}@{domain}"
        return self._generate_hash(email)[:8] + '@example.com'
    
    def _hash_name(self, name: str) -> str:
        """Generate realistic but anonymized names"""
        hash_val = int(self._generate_hash(name)[:4], 16)
        names = ['John Smith', 'Jane Doe', 'Mike Johnson', 'Sarah Wilson']
        return names[hash_val % len(names)]
    
    def _generate_hash(self, value: str) -> str:
        """Generate consistent hash for a value"""
        return hashlib.md5(value.encode()).hexdigest()
    
    def scan_for_pii(self, data: Any) -> List[Dict[str, str]]:
        """Scan data for potential PII violations"""
        violations = []
        
        def scan_value(value: Any, path: str = ''):
            if isinstance(value, str):
                for pii_type, pattern in self.pii_patterns.items():
                    if re.findall(pattern, value):
                        violations.append({
                            'type': pii_type,
                            'path': path,
                            'value': value[:20] + '...' if len(value) > 20 else value
                        })
            elif isinstance(value, dict):
                for key, val in value.items():
                    scan_value(val, f"{path}.{key}" if path else key)
            elif isinstance(value, list):
                for i, val in enumerate(value):
                    scan_value(val, f"{path}[{i}]" if path else f"[{i}]")
        
        scan_value(data)
        return violations
    
    def validate_privacy_compliance(self, file_path: str) -> Dict[str, Any]:
        """Validate that a data file complies with privacy standards"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            violations = self.scan_for_pii(data)
            
            return {
                'file': file_path,
                'scan_date': datetime.now().isoformat(),
                'compliant': len(violations) == 0,
                'violation_count': len(violations),
                'violations': violations[:5]  # Limit output
            }
        
        except Exception as e:
            return {'file': file_path, 'error': str(e), 'compliant': False}
    
    def create_privacy_compliant_dataset(self, source_file: str, output_file: str) -> Dict[str, Any]:
        """Create a privacy-compliant version of a dataset"""
        with open(source_file, 'r') as f:
            data = json.load(f)
        
        # Anonymize the data
        if isinstance(data, list):
            anonymized_data = [self.anonymize_data(item) for item in data]
        else:
            anonymized_data = self.anonymize_data(data)
        
        # Save anonymized version
        with open(output_file, 'w') as f:
            json.dump({
                'data': anonymized_data,
                'metadata': {
                    'anonymized': True,
                    'created_at': datetime.now().isoformat(),
                    'privacy_compliant': True
                }
            }, f, indent=2, default=str)
        
        return {
            'source_file': source_file,
            'output_file': output_file,
            'records_anonymized': len(anonymized_data) if isinstance(anonymized_data, list) else 1
        }

if __name__ == '__main__':
    manager = PrivacyCompliantDataManager()
    print("✅ Privacy compliance manager initialized")
