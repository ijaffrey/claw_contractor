#!/usr/bin/env python3
"""
Unit tests for CacheManager (enrichment cache)
Tests TTL expiration, file handling, and cache operations
"""

import pytest
import json
import os
import tempfile
import time
from unittest.mock import Mock, patch
from cache_manager import CacheManager


class TestEnrichmentCache:
    """Test suite for CacheManager enrichment cache"""
    
    def setup_method(self):
        """Setup test fixtures with temporary cache file"""
        self.temp_file = tempfile.mktemp(suffix='.json')
        self.cache = CacheManager(cache_file=self.temp_file)
    
    def teardown_method(self):
        """Cleanup temporary files"""
        if os.path.exists(self.temp_file):
            os.unlink(self.temp_file)
    
    def test_compound_key_creation(self):
        """Test compound key creation from company name and license"""
        key = self.cache._make_compound_key('ABC Company', 'LIC123')
        assert key == 'ABC Company:LIC123'
        
        # Test with special characters
        key = self.cache._make_compound_key('Company:Special', 'LIC:456')
        assert key == 'Company_Special:LIC_456'
    
    def test_get_cache_miss(self):
        """Test cache miss returns None"""
        result = self.cache.get('NonExistent', 'Company')
        assert result is None
    
    def test_set_and_get_cache_hit(self):
        """Test setting and getting cache entries"""
        data = {'website': 'https://example.com', 'email': 'info@example.com'}
        
        self.cache.set('Test Company', 'LIC123', data)
        result = self.cache.get('Test Company', 'LIC123')
        
        assert result == data
    
    @patch('cache_manager.time.time')
    def test_ttl_expiration(self, mock_time):
        """Test TTL expiration of cache entries"""
        # Set initial time
        current_time = 1000.0
        mock_time.return_value = current_time
        
        data = {'website': 'https://example.com'}
        self.cache.set('Test Company', 'LIC123', data)
        
        # Verify cache hit when within TTL
        result = self.cache.get('Test Company', 'LIC123')
        assert result == data
        
        # Move time forward beyond TTL (31 days)
        mock_time.return_value = current_time + (31 * 24 * 60 * 60)
        
        # Should be cache miss due to expiration
        result = self.cache.get('Test Company', 'LIC123')
        assert result is None
    
    def test_file_persistence(self):
        """Test cache data persistence to file"""
        data = {'website': 'https://example.com', 'email': 'test@example.com'}
        
        # Set data and verify file is created
        self.cache.set('Test Company', 'LIC123', data)
        assert os.path.exists(self.temp_file)
        
        # Create new cache instance and verify data loads
        new_cache = CacheManager(cache_file=self.temp_file)
        result = new_cache.get('Test Company', 'LIC123')
        assert result == data
    
    @patch('builtins.open', side_effect=PermissionError('Permission denied'))
    def test_file_permission_error(self, mock_file):
        """Test handling of file permission errors"""
        # Should not crash on permission error
        cache = CacheManager(cache_file='/invalid/path/cache.json')
        
        # Operations should continue to work in memory
        cache.set('Test', 'LIC123', {'data': 'test'})
        result = cache.get('Test', 'LIC123')
        assert result == {'data': 'test'}
    
    def test_cache_size_tracking(self):
        """Test cache size tracking"""
        assert self.cache.size() == 0
        
        self.cache.set('Company1', 'LIC1', {'data': 'test1'})
        assert self.cache.size() == 1
        
        self.cache.set('Company2', 'LIC2', {'data': 'test2'})
        assert self.cache.size() == 2
