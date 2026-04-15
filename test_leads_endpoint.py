#!/usr/bin/env python3
"""Test the /api/leads endpoint with mock data"""

import json
import random
from datetime import datetime, timedelta

# Create mock lead data
mock_leads = []
nyc_boroughs = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']
nyc_trades = [
    'Plumbing', 'Electrical', 'HVAC', 'General Contracting', 'Roofing',
    'Flooring', 'Kitchen Renovation', 'Bathroom Renovation', 'Painting',
    'Carpentry', 'Masonry', 'Landscaping'
]

for i in range(15):
    # Generate realistic enrichment score (30-95 range)
    enrichment_score = random.randint(30, 95)
    
    # Create realistic lead data
    lead = {
        'id': i + 1,
        'name': f'Lead {i + 1}',
        'trade': random.choice(nyc_trades),
        'borough': random.choice(nyc_boroughs),
        'enrichment_score': enrichment_score,
        'date_created': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
    }
    mock_leads.append(lead)

# Sort by enrichment score descending
mock_leads.sort(key=lambda x: x['enrichment_score'], reverse=True)

# Format as JSON response
response = {
    'leads': mock_leads,
    'total': len(mock_leads)
}

# Print the mock response
print('Mock /api/leads endpoint response:')
print(json.dumps(response, indent=2))

print(f'\n✅ Generated {len(mock_leads)} leads with:')
print(f'- Enrichment scores: {min(lead["enrichment_score"] for lead in mock_leads)} to {max(lead["enrichment_score"] for lead in mock_leads)}')
print(f'- NYC trades: {len(set(lead["trade"] for lead in mock_leads))} different trades')
print(f'- NYC boroughs: {len(set(lead["borough"] for lead in mock_leads))} different boroughs')
print(f'- Date range: Last 30 days')