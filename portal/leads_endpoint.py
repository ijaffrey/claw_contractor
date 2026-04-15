@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Return leads with realistic contractor data and enrichment scores."""
    try:
        import random
        from datetime import datetime, timedelta
        from flask import jsonify
        
        # NYC trades for contractors
        trades = [
            'Plumbing', 'Electrical', 'HVAC', 'General Contractor', 'Roofing',
            'Flooring', 'Painting', 'Carpentry', 'Masonry', 'Kitchen Remodeling',
            'Bathroom Remodeling', 'Windows & Doors', 'Siding', 'Drywall',
            'Tile Installation', 'Concrete Work', 'Landscaping', 'Fencing'
        ]
        
        # NYC boroughs
        boroughs = ['Manhattan', 'Brooklyn', 'Queens', 'The Bronx', 'Staten Island']
        
        # Generate mock lead data with realistic enrichment scores (30-95)
        leads = []
        for i in range(25):
            lead_data = {
                'id': i + 1,
                'name': f'{random.choice(["John", "Maria", "David", "Sarah", "Michael", "Jennifer", "Robert", "Lisa", "James", "Patricia"])} {random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"])}',
                'trade': random.choice(trades),
                'borough': random.choice(boroughs),
                'enrichment_score': random.randint(30, 95),
                'date_created': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            }
            leads.append(lead_data)
        
        return jsonify({
            'success': True,
            'data': leads,
            'total': len(leads)
        })
        
    except Exception as e:
        import logging
        logging.error(f'Error fetching leads: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to fetch leads'
        }), 500