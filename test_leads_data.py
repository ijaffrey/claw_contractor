#!/usr/bin/env python3

import sys
import os
sys.path.append('portal')

from leads_endpoint import get_leads_data
import json

def test_leads_data():
    """Test the leads data generation"""
    print("Testing leads endpoint data generation...")
    
    data = get_leads_data()
    
    print(f"Total leads: {len(data)}")
    
    if len(data) > 0:
        sample_lead = data[0]
        print("\nSample lead:")
        print(json.dumps(sample_lead, indent=2))
        
        # Check enrichment score range
        scores = [lead['enrichment_score'] for lead in data]
        print(f"\nEnrichment scores range: {min(scores)} - {max(scores)}")
        
        # Verify required fields
        required_fields = ['name', 'trade', 'borough', 'enrichment_score', 'date_created']
        for field in required_fields:
            if field in sample_lead:
                print(f"✓ {field}: {sample_lead[field]}")
            else:
                print(f"✗ Missing field: {field}")
                
        # Check borough and trade variety
        boroughs = set(lead['borough'] for lead in data)
        trades = set(lead['trade'] for lead in data)
        print(f"\nBoroughs represented: {len(boroughs)} - {sorted(boroughs)}")
        print(f"Trades represented: {len(trades)} - {sorted(trades)}")
        
    else:
        print("No leads generated!")
        return False
    
    return True

if __name__ == '__main__':
    success = test_leads_data()
    sys.exit(0 if success else 1)
