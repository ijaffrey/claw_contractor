import random
from datetime import datetime, timedelta
from flask import jsonify

@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all leads with mock data including realistic enrichment scores"""
    # NYC boroughs
    boroughs = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']
    
    # Common NYC trades
    trades = [
        'Plumbing', 'Electrical', 'HVAC', 'General Contractor', 'Roofing',
        'Flooring', 'Painting', 'Tile Work', 'Kitchen Renovation', 'Bathroom Renovation',
        'Carpentry', 'Drywall', 'Insulation', 'Windows & Doors', 'Masonry'
    ]
    
    # Generate mock leads with realistic enrichment scores (30-95 range)
    leads = []
    for i in range(15):
        # Create realistic name combinations
        first_names = ['John', 'Maria', 'David', 'Sarah', 'Michael', 'Jennifer', 'Robert', 'Lisa', 'James', 'Patricia']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        # Generate enrichment score with realistic distribution (more in 60-85 range)
        score_weights = [0.1, 0.2, 0.4, 0.2, 0.1]  # 30-45, 46-60, 61-75, 76-90, 91-95
        score_ranges = [(30, 45), (46, 60), (61, 75), (76, 90), (91, 95)]
        selected_range = random.choices(score_ranges, weights=score_weights)[0]
        enrichment_score = random.randint(selected_range[0], selected_range[1])
        
        lead = {
            'id': i + 1,
            'name': f"{random.choice(first_names)} {random.choice(last_names)}",
            'trade': random.choice(trades),
            'borough': random.choice(boroughs),
            'enrichment_score': enrichment_score,
            'date_created': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S')
        }
        leads.append(lead)
    
    return jsonify({
        'success': True,
        'count': len(leads),
        'leads': leads
    })
