from portal.leads_endpoint import get_leads_data, get_leads_summary
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': '2024-01-01T00:00:00Z',
        'service': 'claw-contractor-portal'
    })

@app.route('/api/leads')
def api_leads():
    """
    Returns leads data with name, trade, borough, enrichment_score, date_created fields.
    Mock data includes variety of trades and NYC boroughs with realistic enrichment scores (30-95).
    """
    try:
        leads_data = get_leads_data()
        summary = get_leads_summary()
        
        response = {
            'status': 'success',
            'count': len(leads_data),
            'summary': summary,
            'data': leads_data
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to fetch leads: {str(e)}',
            'data': []
        }), 500

@app.route('/api/leads/summary')
def api_leads_summary():
    """
    Returns summary statistics for leads
    """
    try:
        summary = get_leads_summary()
        return jsonify({
            'status': 'success',
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to fetch summary: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
@app.route('/leads')
def leads():
    """Display leads in a table format"""
    return render_template('leads.html')
