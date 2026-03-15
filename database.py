"""
Database Module
Handles all Supabase interactions for businesses and leads
"""

from supabase import create_client, Client
from config import Config
from datetime import datetime


# Global Supabase client instance
_supabase_client = None


def init_database():
    """
    Initialize Supabase client
    Returns configured Supabase client
    """
    global _supabase_client

    if _supabase_client:
        return _supabase_client

    try:
        _supabase_client = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_KEY
        )
        print("✓ Supabase client initialized")
        return _supabase_client

    except Exception as e:
        print(f"✗ Error initializing Supabase: {e}")
        raise


def get_client():
    """Get or create Supabase client"""
    if not _supabase_client:
        return init_database()
    return _supabase_client


# ============================================================================
# BUSINESS OPERATIONS
# ============================================================================

def insert_business(business_data):
    """
    Insert a new business record

    Args:
        business_data: dict with name, trade_type, brand_voice, email, phone (optional)

    Returns:
        dict: Inserted business record with id
    """
    client = get_client()

    try:
        response = client.table('businesses').insert(business_data).execute()

        if response.data:
            business = response.data[0]
            print(f"✓ Business created: {business['name']} (ID: {business['id']})")
            return business
        else:
            print(f"✗ Failed to create business")
            return None

    except Exception as e:
        print(f"✗ Error inserting business: {e}")
        return None


def get_business(business_id):
    """
    Retrieve business by ID

    Args:
        business_id: UUID of the business

    Returns:
        dict: Business record or None
    """
    client = get_client()

    try:
        response = client.table('businesses').select('*').eq('id', business_id).execute()

        if response.data:
            return response.data[0]
        else:
            print(f"✗ Business not found: {business_id}")
            return None

    except Exception as e:
        print(f"✗ Error retrieving business: {e}")
        return None


def get_business_by_email(email):
    """
    Retrieve business by email address

    Args:
        email: Business email address

    Returns:
        dict: Business record or None
    """
    client = get_client()

    try:
        response = client.table('businesses').select('*').eq('email', email).execute()

        if response.data:
            return response.data[0]
        else:
            return None

    except Exception as e:
        print(f"✗ Error retrieving business by email: {e}")
        return None


def get_all_businesses():
    """
    Retrieve all businesses

    Returns:
        list: All business records
    """
    client = get_client()

    try:
        response = client.table('businesses').select('*').execute()
        return response.data or []

    except Exception as e:
        print(f"✗ Error retrieving businesses: {e}")
        return []


# ============================================================================
# LEAD OPERATIONS
# ============================================================================

def insert_lead(lead_data):
    """
    Insert a new lead record

    Args:
        lead_data: dict with all lead fields:
            - business_id (required)
            - customer_name
            - customer_email
            - phone
            - job_type
            - description
            - location
            - source
            - urgency
            - status (defaults to 'new')
            - raw_subject
            - raw_body
            - email_thread_id
            - email_id

    Returns:
        dict: Inserted lead record with id
    """
    client = get_client()

    # Ensure status is set
    if 'status' not in lead_data:
        lead_data['status'] = 'new'

    try:
        response = client.table('leads').insert(lead_data).execute()

        if response.data:
            lead = response.data[0]
            print(f"✓ Lead created: {lead['customer_name']} - {lead['job_type']} (ID: {lead['id']})")
            return lead
        else:
            print(f"✗ Failed to create lead")
            return None

    except Exception as e:
        print(f"✗ Error inserting lead: {e}")
        return None


def get_lead(lead_id):
    """
    Retrieve lead by ID

    Args:
        lead_id: UUID of the lead

    Returns:
        dict: Lead record or None
    """
    client = get_client()

    try:
        response = client.table('leads').select('*').eq('id', lead_id).execute()

        if response.data:
            return response.data[0]
        else:
            print(f"✗ Lead not found: {lead_id}")
            return None

    except Exception as e:
        print(f"✗ Error retrieving lead: {e}")
        return None


def get_leads(business_id, status=None, limit=100):
    """
    Retrieve leads for a business, optionally filtered by status

    Args:
        business_id: UUID of the business
        status: Optional status filter ('new', 'contacted', 'qualified', etc.)
        limit: Maximum number of leads to retrieve (default 100)

    Returns:
        list: Lead records
    """
    client = get_client()

    try:
        query = client.table('leads').select('*').eq('business_id', business_id)

        if status:
            query = query.eq('status', status)

        response = query.order('created_at', desc=True).limit(limit).execute()

        return response.data or []

    except Exception as e:
        print(f"✗ Error retrieving leads: {e}")
        return []


def update_lead_status(lead_id, status):
    """
    Update lead status (e.g., to 'contacted', 'qualified', 'closed')

    Args:
        lead_id: UUID of the lead
        status: New status value

    Returns:
        dict: Updated lead record or None
    """
    client = get_client()

    try:
        response = client.table('leads').update({
            'status': status
        }).eq('id', lead_id).execute()

        if response.data:
            lead = response.data[0]
            print(f"✓ Lead status updated: {lead_id} -> {status}")
            return lead
        else:
            print(f"✗ Failed to update lead status")
            return None

    except Exception as e:
        print(f"✗ Error updating lead status: {e}")
        return None


def update_lead(lead_id, update_data):
    """
    Update lead with arbitrary fields

    Args:
        lead_id: UUID of the lead
        update_data: dict with fields to update

    Returns:
        dict: Updated lead record or None
    """
    client = get_client()

    try:
        response = client.table('leads').update(update_data).eq('id', lead_id).execute()

        if response.data:
            print(f"✓ Lead updated: {lead_id}")
            return response.data[0]
        else:
            print(f"✗ Failed to update lead")
            return None

    except Exception as e:
        print(f"✗ Error updating lead: {e}")
        return None


def get_lead_by_email_id(email_id):
    """
    Retrieve lead by Gmail email ID (to check if already processed)

    Args:
        email_id: Gmail email ID

    Returns:
        dict: Lead record or None
    """
    client = get_client()

    try:
        response = client.table('leads').select('*').eq('email_id', email_id).execute()

        if response.data:
            return response.data[0]
        else:
            return None

    except Exception as e:
        print(f"✗ Error retrieving lead by email ID: {e}")
        return None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def test_connection():
    """
    Test Supabase connection by querying businesses table

    Returns:
        bool: True if connection successful
    """
    try:
        client = get_client()
        response = client.table('businesses').select('count').execute()
        print(f"✓ Supabase connection successful")
        return True

    except Exception as e:
        print(f"✗ Supabase connection failed: {e}")
        return False
