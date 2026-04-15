from leads_endpoint import get_leads_data
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    """Portal homepage"""
    return '<h1>Portal Home</h1>'

@app.route('/leads')
def leads():
    """Leads management page"""
    leads_data = get_leads_data()
    return render_template('leads.html', leads=leads_data)

@app.route('/api/leads')
def api_leads():
    """API endpoint for leads data"""
    leads_data = get_leads_data()
    return jsonify(leads_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)