#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'portal')

from app import app
import json
from datetime import datetime

def test_leads_api():
    """Test the /api/leads endpoint for required fields and data quality"""
    
    with app.test_client() as client:
        response = client.get('/api/leads')
        
        # Check response status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Parse JSON response
        data = json.loads(response.data)
        
        # Check response structure
        assert data['status'] == 'success', f"Expected success status, got {data.get('status')}"
        assert 'count' in data, "Response missing 'count' field"
        assert 'data' in data, "Response missing 'data' field"
        assert isinstance(data['data'], list), "Data field should be a list"
        
        leads = data['data']
        assert len(leads) > 0, "No leads returned"
        
        # Check required fields in each lead
        required_fields = ['name', 'trade', 'borough', 'enrichment_score', 'date_created']
        
        for i, lead in enumerate(leads[:5]):  # Check first 5 leads
            for field in required_fields:
                assert field in lead, f"Lead {i} missing required field '{field}'"
            
            # Validate enrichment_score range
            score = lead['enrichment_score']
            assert isinstance(score, int), f"Enrichment score should be integer, got {type(score)}"
            assert 30 <= score <= 95, f"Enrichment score {score} outside valid range 30-95"
            
            # Validate date format
            try:
                datetime.strptime(lead['date_created'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                assert False, f"Invalid date format: {lead['date_created']}"
            
            # Validate borough is NYC borough
            nyc_boroughs = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']
            assert lead['borough'] in nyc_boroughs, f"Invalid borough: {lead['borough']}"
        
        print("✅ All API validation tests passed!")
        print(f"✅ Returned {len(leads)} leads with proper structure")
        
        # Show enrichment score distribution
        scores = [lead['enrichment_score'] for lead in leads]
        high_quality = len([s for s in scores if s >= 76])
        medium_quality = len([s for s in scores if 51 <= s <= 75])
        low_quality = len([s for s in scores if 30 <= s <= 50])
        
        print(f"✅ Enrichment score distribution:")
        print(f"   High quality (76-95): {high_quality} leads")
        print(f"   Medium quality (51-75): {medium_quality} leads")
        print(f"   Low quality (30-50): {low_quality} leads")
        print(f"   Range: {min(scores)}-{max(scores)}")
        
        return True

if __name__ == '__main__':
    try:
        test_leads_api()
        print("\n🎉 Lead API validation completed successfully!")
    except AssertionError as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)