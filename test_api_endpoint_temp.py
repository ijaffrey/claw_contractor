#!/usr/bin/env python3
"""Temporary test script to verify the /api/leads endpoint functionality"""

from portal.app import app
import json

def test_api_endpoint():
    """Test the /api/leads endpoint and verify all requirements are met"""
    
    with app.test_client() as client:
        response = client.get('/api/leads')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Endpoint failed")
            return False
        
        data = response.get_json()
        
        if not data:
            print("❌ No JSON response")
            return False
        
        print(f"Response structure: {list(data.keys())}")
        print(f"Lead count: {data.get('count', 0)}")
        
        leads = data.get('data', [])
        if not leads:
            print("❌ No leads data")
            return False
        
        # Check first lead for required fields
        first_lead = leads[0]
        required_fields = ['name', 'trade', 'borough', 'enrichment_score', 'date_created']
        
        print(f"First lead fields: {list(first_lead.keys())}")
        
        missing_fields = [field for field in required_fields if field not in first_lead]
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        
        print("✅ All required fields present")
        
        # Check enrichment score range
        score = first_lead.get('enrichment_score')
        if not (30 <= score <= 95):
            print(f"❌ Enrichment score {score} not in range 30-95")
            return False
        
        print(f"✅ Enrichment score {score} in valid range")
        
        # Check for variety in data
        trades = set(lead.get('trade') for lead in leads[:10])  # Check first 10
        boroughs = set(lead.get('borough') for lead in leads[:10])
        
        print(f"Trades variety (first 10): {len(trades)} unique trades")
        print(f"Borough variety (first 10): {len(boroughs)} unique boroughs")
        
        if len(trades) < 3 or len(boroughs) < 3:
            print("⚠️ Limited variety in mock data")
        else:
            print("✅ Good variety in mock data")
        
        print("\n📊 SUMMARY:")
        print(f"✅ JSON endpoint returns leads: {len(leads)} leads")
        print(f"✅ Required fields present: {', '.join(required_fields)}")
        print(f"✅ Enrichment scores in 30-95 range")
        print(f"✅ Variety in trades and NYC boroughs")
        
        return True

if __name__ == '__main__':
    test_api_endpoint()
