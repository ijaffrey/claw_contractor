#!/usr/bin/env python3
"""Test the /api/leads endpoint"""

import sys
import os
import json

# Add portal to path
sys.path.append('portal')

from app import app

def test_api_endpoint():
    """Test the /api/leads endpoint"""
    with app.test_client() as client:
        response = client.get('/api/leads')
        
        print('Status Code:', response.status_code)
        print('Response Headers:', dict(response.headers))
        
        data = response.get_json()
        print('Response Structure:', type(data))
        
        if data:
            print('Keys:', list(data.keys()))
            
            if 'data' in data and data['data']:
                sample_lead = data['data'][0]
                print('Sample Lead Fields:', list(sample_lead.keys()))
                print('Sample Lead:', json.dumps(sample_lead, indent=2))
                
                # Check required fields
                required_fields = ['name', 'trade', 'borough', 'enrichment_score', 'date_created']
                missing_fields = [f for f in required_fields if f not in sample_lead]
                
                if not missing_fields:
                    print('✅ All required fields present')
                else:
                    print('❌ Missing fields:', missing_fields)
                
                # Check enrichment score range
                scores = [lead['enrichment_score'] for lead in data['data']]
                min_score = min(scores)
                max_score = max(scores)
                print(f'Enrichment score range: {min_score}-{max_score}')
                
                if 30 <= min_score <= 95 and 30 <= max_score <= 95:
                    print('✅ Enrichment scores within 30-95 range')
                else:
                    print('❌ Enrichment scores outside 30-95 range')
                    
                print(f'Total leads: {len(data["data"])}')
                
            else:
                print('No lead data found')
        else:
            print('No response data')

if __name__ == '__main__':
    test_api_endpoint()