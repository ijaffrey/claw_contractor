import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import logging

# Use existing database connection pattern
engine = create_engine(
    os.getenv('DATABASE_URL', 'sqlite:///local.db'),
    pool_pre_ping=True
)

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            angle VARCHAR(255),
            trade VARCHAR(100),
            borough VARCHAR(50),
            lead_count INTEGER DEFAULT 0,
            enriched_count INTEGER DEFAULT 0,
            proposals_sent INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            interested INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.commit()
    print('Campaigns table created successfully')

# Insert sample data
with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO campaigns (name, angle, trade, borough, lead_count, enriched_count, proposals_sent, replies, interested)
        VALUES 
        ('Brooklyn Roofing Blitz', 'Storm damage repairs', 'Roofing', 'Brooklyn', 45, 32, 28, 12, 8),
        ('Manhattan Kitchen Pros', 'Modern renovations', 'Kitchen', 'Manhattan', 23, 18, 15, 7, 4),
        ('Queens HVAC Heroes', 'Energy efficiency', 'HVAC', 'Queens', 67, 55, 41, 19, 11)
    """))
    conn.commit()
    print('Sample campaigns inserted')
