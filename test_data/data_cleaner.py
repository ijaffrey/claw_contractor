#!/usr/bin/env python3
"""
Test Data Cleanup Utilities
Manages cleanup and lifecycle of test data
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

class TestDataCleaner:
    """Manages cleanup and lifecycle of test data"""
    
    def __init__(self, retention_days: int = 7):
        self.retention_days = retention_days
        self.test_data_dir = Path('test_data')
        self.logger = logging.getLogger(__name__)
    
    def clean_old_files(self) -> Dict[str, int]:
        """Remove old test data files"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0
        total_size = 0
        
        for file_path in self.test_data_dir.glob('*.json'):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                file_size = file_path.stat().st_size
                file_path.unlink()
                removed_count += 1
                total_size += file_size
                self.logger.info(f"Removed old test file: {file_path.name}")
        
        return {
            'files_removed': removed_count,
            'bytes_freed': total_size,
            'retention_days': self.retention_days
        }
    
    def clean_test_database(self, db_path: str = 'test_leads.db') -> Dict[str, int]:
        """Clean up test database records"""
        if not os.path.exists(db_path):
            return {'records_removed': 0}
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        cutoff_iso = cutoff_date.isoformat()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Clean old leads
        cursor.execute(
            "DELETE FROM leads WHERE created_at < ?",
            (cutoff_iso,)
        )
        leads_removed = cursor.rowcount
        
        # Clean old conversations
        cursor.execute(
            "DELETE FROM conversations WHERE last_activity < ?",
            (cutoff_iso,)
        )
        conversations_removed = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Cleaned {leads_removed} old leads, {conversations_removed} old conversations")
        
        return {
            'leads_removed': leads_removed,
            'conversations_removed': conversations_removed
        }
    
    def archive_test_data(self, archive_path: Optional[str] = None) -> str:
        """Archive current test data before cleanup"""
        if not archive_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_path = f'test_data/archived_data_{timestamp}.json'
        
        archived_data = {
            'archive_date': datetime.now().isoformat(),
            'retention_days': self.retention_days,
            'files': []
        }
        
        for file_path in self.test_data_dir.glob('*.json'):
            if 'archived_data' not in file_path.name:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                archived_data['files'].append({
                    'filename': file_path.name,
                    'data': data
                })
        
        with open(archive_path, 'w') as f:
            json.dump(archived_data, f, indent=2, default=str)
        
        self.logger.info(f"Test data archived to: {archive_path}")
        return archive_path
    
    def cleanup_all(self, archive_before_cleanup: bool = True) -> Dict[str, Any]:
        """Perform complete cleanup of test data"""
        results = {
            'cleanup_date': datetime.now().isoformat(),
            'archive_path': None,
            'file_cleanup': {},
            'database_cleanup': {}
        }
        
        if archive_before_cleanup:
            results['archive_path'] = self.archive_test_data()
        
        results['file_cleanup'] = self.clean_old_files()
        results['database_cleanup'] = self.clean_test_database()
        
        self.logger.info("Test data cleanup completed")
        return results
    
    def get_cleanup_summary(self) -> Dict[str, Any]:
        """Get summary of test data that would be cleaned"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        files_to_clean = []
        total_size = 0
        
        for file_path in self.test_data_dir.glob('*.json'):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                file_size = file_path.stat().st_size
                files_to_clean.append({
                    'filename': file_path.name,
                    'size': file_size,
                    'age_days': (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days
                })
                total_size += file_size
        
        return {
            'retention_days': self.retention_days,
            'cutoff_date': cutoff_date.isoformat(),
            'files_to_clean': files_to_clean,
            'total_files': len(files_to_clean),
            'total_size_bytes': total_size
        }

if __name__ == '__main__':
    cleaner = TestDataCleaner(retention_days=7)
    summary = cleaner.get_cleanup_summary()
    print(f"Files to clean: {summary['total_files']}")
    print(f"Total size: {summary['total_size_bytes']} bytes")
    
    if summary['total_files'] > 0:
        results = cleaner.cleanup_all(archive_before_cleanup=True)
        print(f"✅ Cleanup completed. Archive: {results['archive_path']}")
    else:
        print("✅ No cleanup needed.")
