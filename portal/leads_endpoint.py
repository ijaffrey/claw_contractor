import random
from datetime import datetime, timedelta
from flask import jsonify
import logging

# NYC Boroughs
BOROUGHS = [
    'Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'
]

# Contractor trades
TRADES = [
    'Plumbing', 'Electrical', 'HVAC', 'General Contractor', 'Roofing',
    'Flooring', 'Painting', 'Carpentry', 'Masonry', 'Landscaping',
    'Kitchen Renovation', 'Bathroom Renovation', 'Windows & Doors'
]

# Sample contractor names
CONTRACTOR_NAMES = [
    'Mike Johnson', 'Sarah Chen', 'David Rodriguez', 'Lisa Thompson',
    'James Wilson', 'Maria Garcia', 'Robert Kim', 'Jennifer Lee',
    'Michael Brown', 'Amanda Davis', 'Carlos Martinez', 'Nicole White',
    'Kevin Murphy', 'Rachel Green', 'Tony Ricci', 'Samantha Jones'
]

def generate_realistic_enrichment_score():
    """Generate enrichment scores with realistic distribution (30-95 range)"""
    # Weight distribution: higher scores are less common
    weights = [0.05, 0.15, 0.25, 0.30, 0.20, 0.05]  # 30-39, 40-49, 50-59, 60-69, 70-79, 80-95
    ranges = [(30, 39), (40, 49), (50, 59), (60, 69), (70, 79), (80, 95)]
    
    selected_range = random.choices(ranges, weights=weights)[0]
    return random.randint(selected_range[0], selected_range[1])

def get_leads_data():
    """Generate mock lead data with all required fields"""
    leads = []
    
    # Generate 15-20 leads for variety
    num_leads = random.randint(15, 20)
    
    for i in range(num_leads):
        # Random date within last 30 days
        days_ago = random.randint(0, 30)
        created_date = datetime.now() - timedelta(days=days_ago)
        
        lead = {
            'id': i + 1,
            'name': random.choice(CONTRACTOR_NAMES),
            'trade': random.choice(TRADES),
            'borough': random.choice(BOROUGHS),
            'enrichment_score': generate_realistic_enrichment_score(),
            'date_created': created_date.strftime('%Y-%m-%d %H:%M:%S'),
            # Additional useful fields for dashboard
            'email': f"{random.choice(CONTRACTOR_NAMES).lower().replace(' ', '.')}@example.com",
            'phone': f"+1-{random.randint(212, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'status': random.choice(['new', 'contacted', 'qualified', 'proposal_sent'])
        }
        
        leads.append(lead)
    
    # Sort by date_created (newest first)
    leads.sort(key=lambda x: x['date_created'], reverse=True)
    
    logging.info(f"Generated {len(leads)} mock leads")
    return leads

# For Flask endpoint usage
def leads_endpoint():
    """Flask endpoint wrapper"""
    try:
        data = get_leads_data()
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error generating leads data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate leads data',
            'timestamp': datetime.now().isoformat()
        }), 500