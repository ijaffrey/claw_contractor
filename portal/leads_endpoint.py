import random
from datetime import datetime, timedelta
from flask import jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NYC Boroughs
BOROUGHS = [
    'Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'
]

# Common NYC contractor trades
TRADES = [
    'Plumbing', 'Electrical', 'HVAC', 'General Contracting',
    'Roofing', 'Flooring', 'Painting', 'Carpentry',
    'Kitchen Renovation', 'Bathroom Renovation', 'Masonry',
    'Landscaping', 'Windows & Doors', 'Demolition'
]

# NYC-style company names
COMPANY_NAMES = [
    'Empire State Plumbing', 'Brooklyn Bridge Electric', 'Queens HVAC Pro',
    'Manhattan Renovations', 'Bronx Building Solutions', 'Staten Island Contractors',
    'NYC Premier Electric', 'Big Apple Plumbing', 'Metro Construction Group',
    'Five Borough Builders', 'Hudson Valley HVAC', 'East River Electric',
    'Central Park Contractors', 'Times Square Renovations', 'Williamsburg Works',
    'Astoria Construction', 'Battery Park Builders', 'Harlem Home Solutions'
]

def generate_realistic_enrichment_score():
    """
    Generate realistic enrichment scores between 30-95 with proper distribution:
    - 30-50: Lower quality leads (30% chance)
    - 51-75: Medium quality leads (50% chance) 
    - 76-95: High quality leads (20% chance)
    """
    rand = random.random()
    if rand < 0.3:
        # Lower quality leads (30-50)
        return random.randint(30, 50)
    elif rand < 0.8:
        # Medium quality leads (51-75)
        return random.randint(51, 75)
    else:
        # High quality leads (76-95)
        return random.randint(76, 95)

def get_leads_data():
    """
    Generate mock lead data with all required fields:
    - name: Company/contractor name
    - trade: Type of contractor work
    - borough: NYC borough
    - enrichment_score: Quality score between 30-95
    - date_created: When the lead was created
    """
    leads = []
    
    # Generate 15-25 mock leads for variety
    num_leads = random.randint(15, 25)
    
    for i in range(num_leads):
        # Generate date within last 30 days
        days_ago = random.randint(0, 30)
        date_created = datetime.now() - timedelta(days=days_ago)
        
        lead = {
            'id': i + 1,
            'name': random.choice(COMPANY_NAMES),
            'trade': random.choice(TRADES),
            'borough': random.choice(BOROUGHS),
            'enrichment_score': generate_realistic_enrichment_score(),
            'date_created': date_created.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        leads.append(lead)
    
    # Sort by enrichment_score descending to show highest quality first
    leads.sort(key=lambda x: x['enrichment_score'], reverse=True)
    
    logger.info(f"Generated {len(leads)} mock leads")
    return leads

def get_leads_summary():
    """
    Get summary statistics for the leads
    """
    leads = get_leads_data()
    
    if not leads:
        return {
            'total_leads': 0,
            'avg_enrichment_score': 0,
            'high_quality_leads': 0,
            'trades_represented': 0
        }
    
    enrichment_scores = [lead['enrichment_score'] for lead in leads]
    high_quality_count = len([score for score in enrichment_scores if score >= 76])
    unique_trades = len(set(lead['trade'] for lead in leads))
    
    return {
        'total_leads': len(leads),
        'avg_enrichment_score': round(sum(enrichment_scores) / len(enrichment_scores), 1),
        'high_quality_leads': high_quality_count,
        'trades_represented': unique_trades
    }