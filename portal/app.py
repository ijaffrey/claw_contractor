from leads_endpoint import get_leads_data
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    """Portal homepage"""
    return '<h1>Portal Home</h1>'

@app.route('/leads')
def leads():
    """Leads management page"""
    return render_template('leads.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
