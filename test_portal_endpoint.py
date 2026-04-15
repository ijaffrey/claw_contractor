#!/usr/bin/env python3

import sys
sys.path.append('portal')

from app import app
import json

def test_leads_endpoint():
    """Test the /api/leads endpoint"""
    with app.test_client() as client:
        response = client.get('/api/leads')
        data = response.get_json()
        print(json.dumps(data, indent=2))
        return data

if __name__ == '__main__':
    test_leads_endpoint()
