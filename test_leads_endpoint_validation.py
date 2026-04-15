#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'portal')

from app import app
import json

def test_leads_endpoint():
    """Test the /api/leads endpoint meets acceptance criteria"""
    with app.test_client() as client:
        response = client.get('/api/leads')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"ERROR: Expected 200, got {response.status_code}")
            print(f"Response data: {response.data}")
            return False
            
        data = json.loads(response.data)
        
        # Verify response structure
        required_fields = ['status', 'count', 'data']
        for field in required_fields:
            if field not in data:
                print(f"ERROR: Missing field '{field}' in response")
                return False
                
        if not isinstance(data['data'], list):
            print("ERROR: 'data' field is not a list")
            return False
            
        if len(data['data']) == 0:
            print("ERROR: No leads returned")
            return False
            
        # Verify lead structure
        required_lead_fields = ['name', 'trade', 'borough', 'enrichment_score', 'date_created']
        sample_lead = data['data'][0]
        
        for field in required_lead_fields:
            if field not in sample_lead:
                print(f"ERROR: Missing field '{field}' in lead data")
                return False
                
        # Verify enrichment score range
        scores = [lead['enrichment_score'] for lead in data['data']]
        min_score = min(scores)
        max_score = max(scores)
        
        if min_score < 30 or max_score > 95:
            print(f"ERROR: Enrichment scores out of range (30-95). Found range: {min_score}-{max_score}")
            return False
            
        print(f"SUCCESS: Endpoint returns {len(data['data'])} leads")
        print(f"Enrichment score range: {min_score}-{max_score}")
        print(f"Sample lead: {json.dumps(sample_lead, indent=2)}")
        
        return True

if __name__ == '__main__':
    success = test_leads_endpoint()
    sys.exit(0 if success else 1)
