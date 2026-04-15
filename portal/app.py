from leads_endpoint import get_leads_data
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leads')
def api_leads():
    """JSON endpoint that returns leads with name, trade, borough, enrichment_score, date_created fields"""
    try:
        leads_data = get_leads_data()
        return jsonify({
            'status': 'success',
            'count': len(leads_data),
            'data': leads_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Legacy route for backward compatibility
@app.route('/leads')
def leads():
    leads_data = get_leads_data()
    return render_template('leads.html', leads=leads_data)

if __name__ == '__main__':
    app.run(debug=True)