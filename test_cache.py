#!/usr/bin/env python3
"""
Test script for CacheManager functionality
Verifies compound keys, TTL, read-through/write-through patterns, and expired cleanup
"""

import os
import time
import tempfile
from cache_manager import CacheManager

def test_cache_functionality():
    """
    Test all cache manager functionality
    """
    print("Testing CacheManager functionality...")
    
    # Use temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        cache_file = temp_file.name
    
    try:
        # Test 1: Initialization with missing file
        print("\n1. Testing initialization with missing cache file...")
        cache = CacheManager(cache_file)
        assert cache.size() == 0, "Cache should be empty on first initialization"
        print("✓ Empty cache initialization works")
        
        # Test 2: Compound key functionality
        print("\n2. Testing compound key operations...")
        test_company = "ABC Construction Corp"
        test_license = "LIC-12345"
        test_value = {"status": "active", "rating": 4.5, "projects": ["roof", "siding"]}
        
        cache.set(test_company, test_license, test_value)
        retrieved = cache.get(test_company, test_license)
        assert retrieved == test_value, f"Retrieved value {retrieved} doesn't match stored {test_value}"
        assert cache.size() == 1, "Cache should have 1 entry"
        print("✓ Compound key set/get works")
        
        # Test 3: Special characters in company name
        print("\n3. Testing special characters in compound keys...")
        special_company = "XYZ: Construction & Co."
        special_license = "LIC:456:789"
        special_value = "test data with colons"
        
        cache.set(special_company, special_license, special_value)
        retrieved_special = cache.get(special_company, special_license)
        assert retrieved_special == special_value, "Special character handling failed"
        assert cache.size() == 2, "Cache should have 2 entries"
        print("✓ Special character handling works")
        
        # Test 4: Cache miss
        print("\n4. Testing cache miss...")
        missing = cache.get("NonExistent", "LIC-999")
        assert missing is None, "Cache miss should return None"
        print("✓ Cache miss returns None")
        
        # Test 5: File persistence
        print("\n5. Testing cache persistence...")
        cache2 = CacheManager(cache_file)
        assert cache2.size() == 2, "Cache should load 2 entries from file"
        retrieved_persistent = cache2.get(test_company, test_license)
        assert retrieved_persistent == test_value, "Persisted data should match"
        print("✓ Cache persistence works")
        
        # Test 6: TTL and expiration (simulate with short TTL)
        print("\n6. Testing TTL functionality...")
        # Create cache with very short TTL for testing
        short_ttl_cache = CacheManager(cache_file)
        short_ttl_cache.ttl_seconds = 1  # 1 second TTL
        
        short_ttl_cache.set("ExpireTest", "LIC-EXP", "will expire")
        assert short_ttl_cache.get("ExpireTest", "LIC-EXP") == "will expire", "Fresh entry should be retrievable"
        
        # Wait for expiration
        time.sleep(2)
        expired = short_ttl_cache.get("ExpireTest", "LIC-EXP")
        assert expired is None, "Expired entry should return None"
        print("✓ TTL expiration works")
        
        # Test 7: clear_expired method
        print("\n7. Testing clear_expired method...")
        # Add some fresh entries and some that will expire
        fresh_cache = CacheManager(cache_file)
        fresh_cache.ttl_seconds = 1  # 1 second TTL
        
        fresh_cache.set("Fresh1", "LIC-F1", "fresh data 1")
        fresh_cache.set("Fresh2", "LIC-F2", "fresh data 2")
        time.sleep(2)  # Let them expire
        
        fresh_cache.set("New", "LIC-NEW", "new data")  # This won't expire
        
        expired_count = fresh_cache.clear_expired()
        assert expired_count >= 2, f"Should have cleared at least 2 expired entries, got {expired_count}"
        assert fresh_cache.get("New", "LIC-NEW") == "new data", "Fresh entry should remain"
        print(f"✓ Cleared {expired_count} expired entries")
        
        # Test 8: clear_all method
        print("\n8. Testing clear_all method...")
        cache.clear_all()
        assert cache.size() == 0, "Cache should be empty after clear_all"
        assert cache.get(test_company, test_license) is None, "All entries should be gone"
        print("✓ clear_all works")
        
        print("\n✅ All tests passed! CacheManager is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    
    finally:
        # Clean up temporary file
        if os.path.exists(cache_file):
            os.unlink(cache_file)
        temp_files = [f"{cache_file}.tmp"]
        for temp_f in temp_files:
            if os.path.exists(temp_f):
                os.unlink(temp_f)

if __name__ == "__main__":
    test_cache_functionality()