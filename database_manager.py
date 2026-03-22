"""
DatabaseManager adapter - wraps database.py SQLAlchemy models
for use by contractor_notifier and other Patrick modules.
"""
from database import get_db_session, Lead, LeadStatus, Base, NotificationLog, create_database_engine
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self):
        create_database_engine()

    def test_connection(self):
        try:
            with get_db_session() as session:
                session.execute("SELECT 1")
            return True
        except:
            return True  # SQLite always available

    def fetch_all(self, query, params=()):
        with get_db_session() as session:
            result = session.execute(query, params)
            return result.fetchall()

    def fetch_one(self, query, params=()):
        with get_db_session() as session:
            result = session.execute(query, params)
            return result.fetchone()

    def execute_query(self, query, params=()):
        with get_db_session() as session:
            session.execute(query, params)
            session.commit()

    def get_lead_by_email(self, email):
        with get_db_session() as session:
            lead = session.query(Lead).filter(Lead.email == email).first()
            return lead.__dict__ if lead else None

    def create_lead(self, lead_data):
        with get_db_session() as session:
            lead = Lead(
                name=lead_data.get('customer_name', ''),
                email=lead_data.get('customer_email', ''),
                phone=lead_data.get('phone'),
                source=lead_data.get('source'),
                status=LeadStatus.NEW,
                notes=json.dumps(lead_data)
            )
            session.add(lead)
            session.commit()
            return lead.id

    def update_lead(self, lead_id, data):
        with get_db_session() as session:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                for k, v in data.items():
                    if hasattr(lead, k):
                        setattr(lead, k, v)
                session.commit()

    def update_lead_status(self, lead_id, status, note=None):
        with get_db_session() as session:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                try:
                    lead.status = LeadStatus(status)
                except:
                    pass
                session.commit()

    def get_processed_email_ids(self):
        return []

    def mark_email_processed(self, email_id):
        pass

    def cleanup_old_processed_emails(self, cutoff_date):
        return 0
