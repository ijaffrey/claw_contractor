import random
from datetime import datetime, timedelta
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

def get_leads_data():
    """Generate mock lead data with realistic enrichment scores (30-95 range)"""
    
    # NYC boroughs for variety
    boroughs = [
        'Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island',
        'Long Island City', 'Williamsburg', 'Astoria', 'Flushing',
        'Bay Ridge', 'Park Slope', 'Crown Heights', 'Bushwick'
    ]
    
    # Construction trades
    trades = [
        'General Contractor', 'Electrician', 'Plumber', 'HVAC Technician',
        'Roofer', 'Flooring Contractor', 'Painter', 'Carpenter',
        'Demolition', 'Masonry', 'Drywall', 'Kitchen Renovation',
        'Bathroom Renovation', 'Windows & Doors', 'Concrete Work',
        'Landscaping', 'Fencing', 'Tile Work', 'Insulation'
    ]
    
    # First and last names for realistic leads
    first_names = [
        'Michael', 'Sarah', 'David', 'Jennifer', 'Robert', 'Lisa',
        'James', 'Maria', 'John', 'Patricia', 'Christopher', 'Linda',
        'Daniel', 'Barbara', 'Matthew', 'Susan', 'Anthony', 'Jessica',
        'Mark', 'Karen', 'Donald', 'Nancy', 'Steven', 'Betty'
    ]
    
    last_names = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
        'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez',
        'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas',
        'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez',
        'Thompson', 'White', 'Harris', 'Sanchez', 'Clark'
    ]
    
    leads = []
    
    # Generate 25-35 leads for good variety
    num_leads = random.randint(25, 35)
    
    for i in range(num_leads):
        # Create realistic enrichment score distribution
        # Higher probability for middle ranges (40-80), lower for extremes
        score_ranges = [
            (30, 39, 0.1),   # 10% chance for low scores
            (40, 59, 0.3),   # 30% chance for medium-low scores
            (60, 79, 0.4),   # 40% chance for medium-high scores
            (80, 95, 0.2)    # 20% chance for high scores
        ]
        
        rand = random.random()
        cumulative = 0
        enrichment_score = 50  # default
        
        for min_score, max_score, probability in score_ranges:
            cumulative += probability
            if rand <= cumulative:
                enrichment_score = random.randint(min_score, max_score)
                break
        
        # Generate date within last 30 days
        days_ago = random.randint(0, 30)
        date_created = (datetime.now() - timedelta(days=days_ago)).isoformat()
        
        lead = {
            'name': f"{random.choice(first_names)} {random.choice(last_names)}",
            'trade': random.choice(trades),
            'borough': random.choice(boroughs),
            'enrichment_score': enrichment_score,
            'date_created': date_created
        }
        
        leads.append(lead)
    
    # Sort by enrichment score descending for better display
    leads.sort(key=lambda x: x['enrichment_score'], reverse=True)
    
    logger.info(f"Generated {len(leads)} mock leads with enrichment scores 30-95")
    
    return leads