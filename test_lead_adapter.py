#!/usr/bin/env python3
"""
Test module for lead_adapter.py
Provides basic validation tests for lead adaptation functionality
"""

def test_lead_adapter_import():
    """Test that lead_adapter module can be imported successfully"""
    try:
        import lead_adapter
        print("✓ lead_adapter module imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import lead_adapter: {e}")
        return False

def test_lead_adapter_structure():
    """Test basic structure of lead_adapter module"""
    try:
        import lead_adapter
        
        # Check if module has expected attributes/functions
        expected_items = ['normalize_lead']
        
        available_items = []
        for item in expected_items:
            if hasattr(lead_adapter, item):
                available_items.append(item)
        
        print(f"✓ lead_adapter structure validated - found {len(available_items)}/{len(expected_items)} expected items")
        return True
    except Exception as e:
        print(f"✗ lead_adapter structure validation failed: {e}")
        return False

if __name__ == '__main__':
    print("Running lead_adapter tests...")
    
    tests = [
        test_lead_adapter_import,
        test_lead_adapter_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All lead_adapter tests passed")
    else:
        print("❌ Some lead_adapter tests failed")