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
            (60, 80, 0.4),   # 40% chance for medium-high scores
            (81, 95, 0.2)    # 20% chance for high scores
        ]
        
        # Select score range based on probabilities
        rand_val = random.random()
        cumulative_prob = 0
        selected_range = None
        
        for min_score, max_score, prob in score_ranges:
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                selected_range = (min_score, max_score)
                break
        
        if not selected_range:
            selected_range = (60, 80)  # Default to medium-high
        
        enrichment_score = random.randint(selected_range[0], selected_range[1])
        
        # Generate realistic date (last 30 days)
        days_ago = random.randint(0, 30)
        date_created = datetime.now() - timedelta(days=days_ago)
        
        lead = {
            'name': f"{random.choice(first_names)} {random.choice(last_names)}",
            'trade': random.choice(trades),
            'borough': random.choice(boroughs),
            'enrichment_score': enrichment_score,
            'date_created': date_created.isoformat()
        }
        
        leads.append(lead)
    
    logger.info(f"Generated {len(leads)} mock leads with enrichment scores 30-95")
    return leads
