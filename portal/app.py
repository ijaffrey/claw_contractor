from portal.leads_endpoint import get_leads_data
import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request, render_template, abort
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from drafted.enrichment_engine import enrich_lead
from sqlalchemy import text
from drafted.enrichment_engine import enrich_lead
from sqlalchemy import text
from drafted.proposal_generator import generate_proposal
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy import text
from drafted.proposal_generator import generate_proposal
import random
from datetime import datetime, timedelta
from flask import jsonify
import random
from datetime import datetime, timedelta
from flask import jsonify
import logging

app = Flask(__name__)

@app.route('/')
def index():
    """Portal homepage"""
    return render_template('portal/index.html')

@app.route('/api/leads', methods=['GET'])
def api_leads():
    """Get leads data with enrichment scores"""
    try:
        leads = get_leads_data()
        return jsonify({
            'success': True,
            'data': leads,
            'total': len(leads)
        })
    except Exception as e:
        logging.error(f'Error fetching leads: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to fetch leads'
        }), 500

@app.route("/api/leads-mock", methods=["GET"])
def api_leads_mock():
    """Get leads data with enrichment scores"""
    return get_leads_data()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
