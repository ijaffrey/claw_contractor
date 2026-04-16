import random
from datetime import datetime, timedelta
from flask import jsonify
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_leads_data():
    """Generate mock lead data with realistic enrichment scores (30-95) and NYC boroughs."""
    
    # NYC boroughs
    boroughs = [
        'Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'
    ]
    
    # Contractor trades
    trades = [
        'Plumbing', 'Electrical', 'HVAC', 'General Contracting', 
        'Roofing', 'Flooring', 'Kitchen Renovation', 'Bathroom Renovation',
        'Painting', 'Carpentry', 'Masonry', 'Landscaping'
    ]
    
    # First names
    first_names = [
        'Michael', 'Sarah', 'David', 'Jennifer', 'Robert', 'Lisa', 'James', 'Mary',
        'Christopher', 'Patricia', 'Matthew', 'Linda', 'Anthony', 'Barbara', 'Mark',
        'Elizabeth', 'Daniel', 'Jessica', 'Steven', 'Susan', 'Paul', 'Karen', 'Andrew',
        'Nancy', 'Kenneth', 'Betty', 'Joshua', 'Helen', 'Kevin', 'Sandra'
    ]
    
    # Last names
    last_names = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
        'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
        'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson'
    ]
    
    # Generate realistic enrichment scores with weighted distribution
    def generate_enrichment_score():
        # Weight the distribution toward higher scores (60-85 range)
        if random.random() < 0.6:  # 60% in good range
            return random.randint(60, 85)
        elif random.random() < 0.8:  # 20% in excellent range
            return random.randint(86, 95)
        else:  # 20% in poor range
            return random.randint(30, 59)
    
    leads = []
    num_leads = random.randint(8, 15)
    
    for i in range(num_leads):
        # Create realistic date within last 30 days
        days_ago = random.randint(0, 30)
        date_created = datetime.now() - timedelta(days=days_ago)
        
        lead = {
            'name': f"{random.choice(first_names)} {random.choice(last_names)}",
            'trade': random.choice(trades),
            'borough': random.choice(boroughs),
            'enrichment_score': generate_enrichment_score(),
            'date_created': date_created.strftime('%Y-%m-%d')
        }
        
        leads.append(lead)
    
    # Sort by date_created descending (newest first)
    leads.sort(key=lambda x: x['date_created'], reverse=True)
    
    logger.info(f"Generated {len(leads)} mock leads with enrichment scores ranging 30-95")
    
    # Return structured JSON response
    return {
        'status': 'success',
        'data': leads,
        'count': len(leads)
    }
