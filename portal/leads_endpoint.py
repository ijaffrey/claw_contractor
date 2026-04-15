import random
from datetime import datetime, timedelta
from flask import jsonify
import logging

# NYC boroughs for realistic data
BOROUGHS = [
    'Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'
]

# Construction trades
TRADES = [
    'General Contractor', 'Electrical', 'Plumbing', 'HVAC',
    'Roofing', 'Flooring', 'Painting', 'Carpentry', 'Masonry',
    'Drywall', 'Kitchen Renovation', 'Bathroom Renovation',
    'Landscaping', 'Concrete', 'Insulation', 'Windows & Doors'
]

# Lead names for variety
LEAD_NAMES = [
    'John Martinez', 'Sarah Chen', 'Michael Rodriguez', 'Emily Johnson',
    'David Kim', 'Lisa Thompson', 'Robert Garcia', 'Jennifer Lee',
    'Christopher Brown', 'Amanda Davis', 'Daniel Wilson', 'Jessica Taylor',
    'Matthew Anderson', 'Ashley Miller', 'Anthony Jackson', 'Stephanie White'
]

def get_leads_data():
    """Generate mock lead data with all required fields."""
    leads = []
    
    # Generate 50 leads with realistic distribution
    for i in range(50):
        # Create realistic enrichment score distribution (30-95)
        # Most scores should be in 60-85 range with some outliers
        score_rand = random.random()
        if score_rand < 0.1:  # 10% low scores (30-50)
            enrichment_score = random.randint(30, 50)
        elif score_rand < 0.2:  # 10% very high scores (85-95)
            enrichment_score = random.randint(85, 95)
        else:  # 80% medium-high scores (55-84)
            enrichment_score = random.randint(55, 84)
        
        # Random date within last 30 days
        days_ago = random.randint(0, 30)
        date_created = datetime.now() - timedelta(days=days_ago)
        
        lead = {
            'id': i + 1,
            'name': random.choice(LEAD_NAMES),
            'trade': random.choice(TRADES),
            'borough': random.choice(BOROUGHS),
            'enrichment_score': enrichment_score,
            'date_created': date_created.isoformat()
        }
        leads.append(lead)
    
    # Sort by enrichment score descending for better display
    leads.sort(key=lambda x: x['enrichment_score'], reverse=True)
    
    return leads
