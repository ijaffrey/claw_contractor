#!/usr/bin/env python3
"""
Leads table creation script for NYC DOB contractor data
Based on analysis of NYC DOB API response structure and existing SQLite database patterns
"""

import os
import sys

sys.path.append(".")
from database import get_db_session, Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, DECIMAL, Date
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NYCDOBLead(Base):
    """NYC DOB Lead table schema based on API response structure"""

    __tablename__ = "nyc_dob_leads"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # NYC DOB API fields (based on sample response analysis)
    job_number = Column(String(50), unique=True, nullable=False, index=True)
    job_type = Column(String(100))
    job_description = Column(Text)

    # Owner information
    owner_name = Column(String(200), index=True)
    owner_phone = Column(String(20))
    owner_business_name = Column(String(200))
    owner_house_number = Column(String(20))
    owner_house_street = Column(String(200))
    owner_city = Column(String(100))
    owner_state = Column(String(10))
    owner_zip = Column(String(10), index=True)

    # Job site information
    site_house_number = Column(String(20))
    site_house_street = Column(String(200))
    site_city = Column(String(100))
    site_state = Column(String(10))
    site_zip = Column(String(10), index=True)

    # Permit information
    work_type = Column(String(100), index=True)
    permit_sequence = Column(Integer)
    permit_subtype = Column(String(100))
    filing_status = Column(String(50))
    status_date = Column(Date, index=True)
    job_start_date = Column(Date)
    permittee_license_number = Column(String(50))
    permittee_license_type = Column(String(50))
    work_on_floor = Column(String(20))
    estimated_job_costs = Column(DECIMAL(12, 2))

    # Lead qualification and tracking
    qualification_score = Column(Integer, default=0, index=True)
    is_qualified = Column(Boolean, default=False, index=True)
    contact_attempted = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<NYCDOBLead(id={self.id}, job_number='{self.job_number}', owner_name='{self.owner_name}')>"


def create_leads_table():
    """Create NYC DOB leads table with proper schema and indexes"""
    try:
        # Get database session using existing pattern
        session = get_db_session()

        # Create the table
        Base.metadata.create_all(bind=session.bind)

        print("✅ NYC DOB leads table created successfully")
        print("📊 Table schema:")
        print("   - job_number (unique, indexed)")
        print("   - owner/site contact information")
        print("   - permit and work details")
        print("   - qualification scoring fields")
        print("   - timestamps for tracking")
        print("\n🔍 Indexes created for:")
        print("   - job_number (unique lookup)")
        print("   - owner_name (search)")
        print("   - owner_zip, site_zip (geographic filtering)")
        print("   - work_type (filtering)")
        print("   - qualification_score (scoring queries)")
        print("   - is_qualified (status filtering)")
        print("   - status_date, created_at (temporal queries)")

        session.close()
        return True

    except Exception as e:
        logger.error(f"Error creating NYC DOB leads table: {e}")
        print(f"❌ Error creating leads table: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Creating NYC DOB Leads table...")
    print("📋 Based on NYC DOB API response structure analysis")
    print("🏗️  Designed for contractor lead management")
    print()

    success = create_leads_table()
    sys.exit(0 if success else 1)
