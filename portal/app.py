from portal.leads_endpoint import get_leads_data
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads')
def api_leads():
    """API endpoint for leads data with realistic enrichment scores."""
    try:
        data = get_leads_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': 'Failed to fetch leads data',
            'data': [],
            'count': 0
        }), 500

@app.route('/api/campaigns')
def api_campaigns():
    """Mock campaigns endpoint for testing."""
    mock_campaigns = {
        'status': 'success',
        'data': [
            {'id': 1, 'name': 'Summer Renovation Campaign', 'status': 'active'},
            {'id': 2, 'name': 'Kitchen Remodel Outreach', 'status': 'paused'}
        ],
        'count': 2
    }
    return jsonify(mock_campaigns)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'contractor-portal'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
