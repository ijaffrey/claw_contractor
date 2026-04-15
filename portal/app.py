from leads_endpoint import get_leads_data
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads')
def api_leads():
    """JSON endpoint that returns leads with all required fields."""
    try:
        leads = get_leads_data()
        return jsonify({
            'status': 'success',
            'data': leads,
            'count': len(leads)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/leads')
def leads_page():
    return render_template('leads.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
