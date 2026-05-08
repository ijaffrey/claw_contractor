#!/usr/bin/env python3
"""
JSON File-Based Cache Manager
Implements compound key caching with TTL and read-through/write-through patterns
"""

import json
import os
import time
from typing import Any, Dict, Optional, Set
import logging

# Configure logging
logger = logging.getLogger(__name__)

class CacheManager:
    """
    JSON file-based cache with compound keys, 30-day TTL, and read-through/write-through operations
    """
    
    def __init__(self, cache_file: str = 'cache_data.json'):
        """
        Initialize cache manager
        
        Args:
            cache_file: Path to JSON cache file
        """
        self.cache_file = cache_file
        self.ttl_days = 30
        self.ttl_seconds = self.ttl_days * 24 * 60 * 60  # 30 days in seconds
        self._cache_data: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
        
        logger.info(f"CacheManager initialized with file: {cache_file}, TTL: {self.ttl_days} days")
    
    def _make_compound_key(self, company_name: str, license_number: str) -> str:
        """
        Create compound key in format 'company_name:license_number'
        Handles special characters by replacing colons with underscores
        
        Args:
            company_name: Company name
            license_number: License number
            
        Returns:
            Compound key string
        """
        # Replace colons to avoid confusion with key separator
        clean_company = company_name.replace(':', '_') if company_name else ''
        clean_license = license_number.replace(':', '_') if license_number else ''
        
        return f"{clean_company}:{clean_license}"
    
    def _get_current_timestamp(self) -> float:
        """
        Get current Unix timestamp
        
        Returns:
            Current timestamp as float
        """
        return time.time()
    
    def _is_expired(self, timestamp: float) -> bool:
        """
        Check if a timestamp is expired (older than TTL)
        
        Args:
            timestamp: Unix timestamp to check
            
        Returns:
            True if expired, False otherwise
        """
        current_time = self._get_current_timestamp()
        return (current_time - timestamp) > self.ttl_seconds
    
    def _load_cache(self):
        """
        Load cache data from JSON file
        Handles missing file as empty cache
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self._cache_data = json.load(f)
                logger.info(f"Loaded cache with {len(self._cache_data)} entries")
            else:
                self._cache_data = {}
                logger.info("No cache file found, starting with empty cache")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading cache file {self.cache_file}: {e}")
            self._cache_data = {}
    
    def _save_cache(self):
        """
        Save cache data to JSON file with atomic write
        """
        try:
            # Write to temporary file first for atomic operation
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(self._cache_data, f, indent=2)
            
            # Move temp file to actual cache file
            os.replace(temp_file, self.cache_file)
            logger.debug(f"Cache saved with {len(self._cache_data)} entries")
        except (IOError, OSError) as e:
            logger.error(f"Error saving cache file {self.cache_file}: {e}")
    
    def get(self, company_name: str, license_number: str) -> Optional[Any]:
        """
        Read-through cache operation
        Returns cached value if exists and not expired, None otherwise
        
        Args:
            company_name: Company name for compound key
            license_number: License number for compound key
            
        Returns:
            Cached value or None if not found/expired
        """
        key = self._make_compound_key(company_name, license_number)
        
        if key not in self._cache_data:
            logger.debug(f"Cache miss for key: {key}")
            return None
        
        entry = self._cache_data[key]
        timestamp = entry.get('timestamp', 0)
        
        if self._is_expired(timestamp):
            logger.debug(f"Cache entry expired for key: {key}")
            # Remove expired entry
            del self._cache_data[key]
            self._save_cache()
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return entry.get('value')
    
    def set(self, company_name: str, license_number: str, value: Any):
        """
        Write-through cache operation
        Stores value with current timestamp for TTL tracking
        
        Args:
            company_name: Company name for compound key
            license_number: License number for compound key
            value: Value to cache
        """
        key = self._make_compound_key(company_name, license_number)
        timestamp = self._get_current_timestamp()
        
        self._cache_data[key] = {
            'value': value,
            'timestamp': timestamp
        }
        
        self._save_cache()
        logger.debug(f"Cache entry set for key: {key}")
    
    def clear_expired(self) -> int:
        """
        Remove all expired entries from cache
        
        Returns:
            Number of entries removed
        """
        expired_keys = []
        current_time = self._get_current_timestamp()
        
        for key, entry in self._cache_data.items():
            timestamp = entry.get('timestamp', 0)
            if self._is_expired(timestamp):
                expired_keys.append(key)
        
        # Remove expired entries
        for key in expired_keys:
            del self._cache_data[key]
        
        if expired_keys:
            self._save_cache()
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def size(self) -> int:
        """
        Get current cache size
        
        Returns:
            Number of entries in cache
        """
        return len(self._cache_data)
    
    def clear_all(self):
        """
        Clear all cache entries
        """
        self._cache_data = {}
        self._save_cache()
        logger.info("Cache cleared completely")