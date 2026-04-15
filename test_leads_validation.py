#!/usr/bin/env python3
"""Test script to validate leads endpoint functionality"""

import sys
sys.path.insert(0, '.')

from portal.leads_endpoint import get_leads_data

def test_leads_endpoint():
    """Test the leads endpoint functionality"""
    try:
        result = get_leads_data()
        
        if not result.get('success'):
            print("✗ Endpoint returned success=False")
            return False
            
        leads = result.get('leads', [])
        if len(leads) == 0:
            print("✗ No leads data returned")
            return False
            
        # Check first 5 leads for enrichment scores
        valid_scores = True
        sample_scores = []
        
        for i, lead in enumerate(leads[:5]):
            if 'enrichment_score' not in lead:
                print(f"✗ Lead {i+1} missing enrichment_score field")
                valid_scores = False
                break
                
            score = lead['enrichment_score']
            sample_scores.append(score)
            
            if not (30 <= score <= 95):
                print(f"✗ Lead {i+1} enrichment_score {score} outside 30-95 range")
                valid_scores = False
                break
                
        if valid_scores:
            print("✓ Endpoint works successfully")
            print(f"Total leads: {len(leads)}")
            print(f"Sample enrichment scores: {sample_scores}")
            
            # Verify required fields
            first_lead = leads[0]
            required_fields = ['name', 'trade', 'borough', 'enrichment_score', 'date_created']
            missing_fields = [field for field in required_fields if field not in first_lead]
            
            if missing_fields:
                print(f"✗ Missing required fields: {missing_fields}")
                return False
            else:
                print(f"✓ All required fields present: {required_fields}")
                return True
        else:
            return False
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False

if __name__ == '__main__':
    success = test_leads_endpoint()
    sys.exit(0 if success else 1)