#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'portal')

from app import app

def test_campaigns_route():
    with app.test_client() as client:
        response = client.get('/campaigns')
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.data.decode()}")
        else:
            print("Success: /campaigns route works!")
        return response.status_code == 200

if __name__ == '__main__':
    success = test_campaigns_route()
    sys.exit(0 if success else 1)
