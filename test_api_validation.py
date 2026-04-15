#!/usr/bin/env python3
"""Test script to validate the /api/leads endpoint meets all acceptance criteria."""

import sys
import os
import json
sys.path.append('portal')

from app import app
from leads_endpoint import get_leads_data

def test_endpoint():
    """Test the /api/leads endpoint and validate acceptance criteria."""
    print("Testing /api/leads endpoint...")
    
    # Test 1: Check if endpoint works with Flask test client
    with app.test_client() as client:
        response = client.get('/api/leads')
        
        print(f"HTTP Status Code: {response.status_code}")
        assert response.status_code == 200, "Endpoint should return 200 status"
        
        # Parse JSON response
        data = json.loads(response.data)
        print(f"Response status: {data['status']}")
        assert data['status'] == 'success', "Response should have success status"
        
        # Check data structure
        assert 'data' in data, "Response should contain 'data' field"
        assert 'count' in data, "Response should contain 'count' field"
        
        leads = data['data']
        print(f"Total leads returned: {data['count']}")
        
        # Test 2: Validate required fields are present
        required_fields = ['name', 'trade', 'borough', 'enrichment_score', 'date_created']
        if leads:
            sample_lead = leads[0]
            print("Sample lead fields:", list(sample_lead.keys()))
            
            for field in required_fields:
                assert field in sample_lead, f"Missing required field: {field}"
            
            print("✓ All required fields present:", required_fields)
            
            # Test 3: Validate enrichment score range (30-95)
            scores = [lead['enrichment_score'] for lead in leads]
            min_score = min(scores)
            max_score = max(scores)
            avg_score = sum(scores) / len(scores)
            
            print(f"Score distribution:")
            print(f"  Range: {min_score} - {max_score}")
            print(f"  Average: {avg_score:.1f}")
            
            assert min_score >= 30, f"Minimum score {min_score} should be >= 30"
            assert max_score <= 95, f"Maximum score {max_score} should be <= 95"
            print("✓ Enrichment scores in valid range (30-95)")
            
            # Test 4: Validate variety of trades and boroughs
            trades = set(lead['trade'] for lead in leads)
            boroughs = set(lead['borough'] for lead in leads)
            
            print(f"Trade variety: {len(trades)} different trades")
            print(f"Borough variety: {len(boroughs)} different boroughs")
            print(f"Sample trades: {list(trades)[:5]}")
            print(f"Sample boroughs: {list(boroughs)}")
            
            assert len(trades) >= 5, "Should have variety of trades"
            assert len(boroughs) >= 3, "Should have variety of NYC boroughs"
            print("✓ Good variety of trades and NYC boroughs")
            
            # Test 5: Show sample lead
            print("\nSample lead data:")
            print(json.dumps(sample_lead, indent=2))
            
        else:
            print("ERROR: No leads returned!")
            return False
    
    print("\n🎉 ALL ACCEPTANCE CRITERIA MET!")
    print("✓ JSON endpoint returns leads with required fields")
    print("✓ Mock data includes variety of trades and NYC boroughs")
    print("✓ Enrichment scores distributed realistically between 30-95")
    return True

if __name__ == '__main__':
    try:
        success = test_endpoint()
        if success:
            print("\nEndpoint validation: PASSED")
            sys.exit(0)
        else:
            print("\nEndpoint validation: FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\nError during validation: {e}")
        sys.exit(1)
