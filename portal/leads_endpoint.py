import random
from datetime import datetime, timedelta
from flask import jsonify
import logging

# NYC Boroughs
NYC_BOROUGHS = [
    'Manhattan',
    'Brooklyn', 
    'Queens',
    'Bronx',
    'Staten Island'
]

# Realistic contractor trades
CONTRACTOR_TRADES = [
    'General Contractor',
    'Plumbing',
    'Electrical',
    'HVAC',
    'Roofing',
    'Flooring',
    'Kitchen Renovation',
    'Bathroom Renovation',
    'Painting',
    'Carpentry',
    'Masonry',
    'Waterproofing',
    'Insulation',
    'Windows & Doors',
    'Concrete Work'
]

# Sample lead names
LEAD_NAMES = [
    'Michael Chen',
    'Sarah Rodriguez',
    'David Johnson',
    'Maria Gonzalez',
    'James Wilson',
    'Jennifer Kim',
    'Robert Taylor',
    'Lisa Anderson',
    'Anthony Martinez',
    'Michelle Thompson',
    'Christopher Lee',
    'Amanda White',
    'Daniel Brown',
    'Jessica Davis',
    'Matthew Garcia'
]

def generate_realistic_enrichment_score():
    """Generate enrichment scores with realistic distribution (30-95 range)"""
    # Weight distribution: more scores in 60-85 range, fewer at extremes
    ranges = [
        (30, 50, 10),  # Low scores: 10% chance
        (50, 70, 40),  # Medium scores: 40% chance  
        (70, 85, 35),  # Good scores: 35% chance
        (85, 95, 15)   # Excellent scores: 15% chance
    ]
    
    rand = random.randint(1, 100)
    cumulative = 0
    
    for min_score, max_score, weight in ranges:
        cumulative += weight
        if rand <= cumulative:
            return random.randint(min_score, max_score)
    
    return random.randint(70, 85)  # Default fallback

def generate_mock_leads(count=25):
    """Generate realistic mock lead data"""
    leads = []
    
    for i in range(count):
        # Create date within last 30 days
        days_ago = random.randint(0, 30)
        date_created = datetime.now() - timedelta(days=days_ago)
        
        lead = {
            'id': i + 1,
            'name': random.choice(LEAD_NAMES),
            'trade': random.choice(CONTRACTOR_TRADES),
            'borough': random.choice(NYC_BOROUGHS),
            'enrichment_score': generate_realistic_enrichment_score(),
            'date_created': date_created.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        leads.append(lead)
    
    # Sort by date created (most recent first)
    leads.sort(key=lambda x: x['date_created'], reverse=True)
    
    return leads

def get_leads_data():
    """Return leads data for the /api/leads endpoint"""
    try:
        leads = generate_mock_leads()
        
        return {
            'success': True,
            'total_count': len(leads),
            'leads': leads,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    except Exception as e:
        logging.error(f"Error generating leads data: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'leads': [],
            'total_count': 0
        }
