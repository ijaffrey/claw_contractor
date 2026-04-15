import random
from datetime import datetime, timedelta
from flask import jsonify
import logging

# NYC boroughs for variety
BOROUGHS = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']

# Contractor trades with good variety
TRADES = [
    'Plumbing', 'Electrical', 'HVAC', 'General Contracting', 'Roofing',
    'Flooring', 'Painting', 'Carpentry', 'Masonry', 'Tile Work',
    'Kitchen Renovation', 'Bathroom Renovation', 'Insulation', 'Drywall',
    'Windows & Doors', 'Landscaping', 'Concrete Work', 'Siding'
]

# First and last names for realistic lead names
FIRST_NAMES = [
    'Michael', 'Sarah', 'David', 'Jennifer', 'Robert', 'Lisa', 'William', 'Karen',
    'James', 'Nancy', 'John', 'Betty', 'Christopher', 'Helen', 'Daniel', 'Sandra',
    'Matthew', 'Donna', 'Anthony', 'Carol', 'Mark', 'Ruth', 'Donald', 'Sharon',
    'Steven', 'Michelle', 'Paul', 'Laura', 'Andrew', 'Emily'
]

LAST_NAMES = [
    'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez',
    'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas',
    'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
    'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker'
]

def generate_realistic_enrichment_score():
    """Generate enrichment scores with realistic distribution (30-95 range)"""
    # Weight towards middle-high scores (60-85) as most realistic
    weights = [5, 10, 15, 25, 20, 15, 10]  # 30-39, 40-49, 50-59, 60-69, 70-79, 80-89, 90-95
    ranges = [(30, 39), (40, 49), (50, 59), (60, 69), (70, 79), (80, 89), (90, 95)]
    
    selected_range = random.choices(ranges, weights=weights)[0]
    return random.randint(selected_range[0], selected_range[1])

def generate_mock_lead():
    """Generate a single mock lead with all required fields"""
    return {
        'name': f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        'trade': random.choice(TRADES),
        'borough': random.choice(BOROUGHS),
        'enrichment_score': generate_realistic_enrichment_score(),
        'date_created': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
    }

def get_leads_data():
    """Generate mock leads data with variety in trades and NYC boroughs"""
    try:
        # Generate 15-25 leads for good variety
        num_leads = random.randint(15, 25)
        leads = [generate_mock_lead() for _ in range(num_leads)]
        
        logging.info(f"Generated {len(leads)} mock leads")
        return leads
        
    except Exception as e:
        logging.error(f"Error generating leads data: {e}")
        return []