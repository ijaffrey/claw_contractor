from leads_endpoint import get_leads_data
from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)

@app.route('/')
def index():
    """Portal homepage"""
    return '<h1>Portal Home</h1>'

@app.route('/leads')
def leads():
    """Leads management page"""
    return render_template('leads.html')

@app.route('/campaigns')
def campaigns():
    """Campaigns management page"""
    # Mock campaign data with trade and borough fields
    campaigns_data = [
        {
            'id': 1,
            'name': 'Manhattan Plumbing Outreach',
            'angle': 'Emergency repairs available 24/7',
            'trade': 'Plumbing',
            'borough': 'Manhattan',
            'lead_count': 45,
            'enriched_count': 38,
            'proposals_sent': 25,
            'replies': 12,
            'interested': 8
        },
        {
            'id': 2,
            'name': 'Brooklyn HVAC Campaign',
            'angle': 'Energy-efficient heating solutions',
            'trade': 'HVAC',
            'borough': 'Brooklyn',
            'lead_count': 32,
            'enriched_count': 28,
            'proposals_sent': 18,
            'replies': 9,
            'interested': 5
        },
        {
            'id': 3,
            'name': 'Queens Electrical Services',
            'angle': 'Licensed electricians for all projects',
            'trade': 'Electrical',
            'borough': 'Queens',
            'lead_count': 27,
            'enriched_count': 22,
            'proposals_sent': 15,
            'replies': 7,
            'interested': 4
        },
        {
            'id': 4,
            'name': 'Bronx General Contracting',
            'angle': 'Full-service construction and renovation',
            'trade': 'General Contracting',
            'borough': 'Bronx',
            'lead_count': 19,
            'enriched_count': 16,
            'proposals_sent': 10,
            'replies': 5,
            'interested': 3
        },
        {
            'id': 5,
            'name': 'Staten Island Plumbing',
            'angle': 'Local plumbers you can trust',
            'trade': 'Plumbing',
            'borough': 'Staten Island',
            'lead_count': 14,
            'enriched_count': 12,
            'proposals_sent': 8,
            'replies': 4,
            'interested': 2
        }
    ]
    return render_template('campaigns.html', campaigns=campaigns_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)