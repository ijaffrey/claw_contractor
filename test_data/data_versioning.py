#!/usr/bin/env python3
"""
Test Data Versioning System
Manages versions and schemas of test data
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

class TestDataVersionManager:
    """Manages versioning and schema evolution of test data"""
    
    def __init__(self, base_dir: str = 'test_data'):
        self.base_dir = Path(base_dir)
        self.versions_dir = self.base_dir / 'versions'
        self.logger = logging.getLogger(__name__)
        self.versions_dir.mkdir(exist_ok=True)
    
    def create_version(self, data_type: str, data: Any, description: str = '') -> str:
        """Create a new version of test data"""
        version_id = self._generate_version_id()
        
        version_info = {
            'version_id': version_id,
            'data_type': data_type,
            'created_at': datetime.now().isoformat(),
            'description': description,
            'record_count': len(data) if isinstance(data, list) else 1,
            'data_hash': self._calculate_data_hash(data)
        }
        
        # Save version info
        version_file = self.versions_dir / f"{data_type}_v{version_id}.json"
        with open(version_file, 'w') as f:
            json.dump({'metadata': version_info, 'data': data}, f, indent=2, default=str)
        
        # Update version registry
        self._update_version_registry(data_type, version_info)
        
        self.logger.info(f"Created version {version_id} for {data_type}")
        return version_id
    
    def get_version(self, data_type: str, version_id: str) -> Dict[str, Any]:
        """Retrieve a specific version of test data"""
        version_file = self.versions_dir / f"{data_type}_v{version_id}.json"
        
        if not version_file.exists():
            raise FileNotFoundError(f"Version {version_id} not found for {data_type}")
        
        with open(version_file, 'r') as f:
            return json.load(f)
    
    def list_versions(self, data_type: str) -> List[Dict[str, Any]]:
        """List all versions for a data type"""
        registry_file = self.versions_dir / f"{data_type}_registry.json"
        
        if not registry_file.exists():
            return []
        
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        
        return registry.get('versions', [])
    
    def get_latest_version(self, data_type: str) -> Optional[Dict[str, Any]]:
        """Get the latest version of test data"""
        versions = self.list_versions(data_type)
        
        if not versions:
            return None
        
        latest = max(versions, key=lambda v: v['created_at'])
        return self.get_version(data_type, latest['version_id'])
    
    def _generate_version_id(self) -> str:
        """Generate a unique version ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{timestamp}_{hashlib.md5(timestamp.encode()).hexdigest()[:8]}"
    
    def _calculate_data_hash(self, data: Any) -> str:
        """Calculate hash of data for change detection"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _update_version_registry(self, data_type: str, version_info: Dict[str, Any]) -> None:
        """Update the version registry for a data type"""
        registry_file = self.versions_dir / f"{data_type}_registry.json"
        
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                registry = json.load(f)
        else:
            registry = {'data_type': data_type, 'versions': []}
        
        registry['versions'].append(version_info)
        registry['last_updated'] = datetime.now().isoformat()
        
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2, default=str)

if __name__ == '__main__':
    version_manager = TestDataVersionManager()
    print("✅ Test data versioning system initialized")
