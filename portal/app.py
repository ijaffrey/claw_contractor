from leads_endpoint import get_leads_data
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads')
def api_leads():
    """API endpoint to return leads data with mock data including realistic enrichment scores"""
    try:
        leads_data = get_leads_data()
        
        response = {
            'status': 'success',
            'count': len(leads_data),
            'data': leads_data
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Additional routes for contractor portal functionality
@app.route('/leads')
def leads_dashboard():
    """Dashboard view for leads management"""
    return render_template('leads_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
