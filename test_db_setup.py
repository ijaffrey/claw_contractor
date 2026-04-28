#!/usr/bin/env python3
"""
Test Database Setup Script
Creates test database with required tables and sample data
"""

import sqlite3
import os
import logging
from test_env_config import TestConfig

logger = logging.getLogger(__name__)


def setup_test_database():
    """Setup test database with required tables"""
    try:
        logger.info("Setting up test database...")

        # Remove existing test database if it exists
        if os.path.exists(TestConfig.TEST_DATABASE_PATH):
            os.remove(TestConfig.TEST_DATABASE_PATH)
            logger.info(
                f"Removed existing test database: {TestConfig.TEST_DATABASE_PATH}"
            )

        # Create new test database
        conn = sqlite3.connect(TestConfig.TEST_DATABASE_PATH)
        cursor = conn.cursor()

        # Create leads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                status TEXT DEFAULT 'new',
                source TEXT DEFAULT 'email',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                thread_id TEXT,
                message_content TEXT,
                sender TEXT,
                direction TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        """)

        # Create notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                type TEXT NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT,
                content TEXT,
                status TEXT DEFAULT 'pending',
                sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        """)

        # Create contractors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contractors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                specialties TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed test data
        cursor.executemany(
            """
            INSERT INTO contractors (name, email, phone, specialties, active)
            VALUES (?, ?, ?, ?, ?)
        """,
            TestConfig.TEST_CONTRACTORS,
        )

        cursor.executemany(
            """
            INSERT INTO leads (name, email, phone, status, source)
            VALUES (?, ?, ?, ?, ?)
        """,
            TestConfig.TEST_LEADS,
        )

        conn.commit()
        conn.close()

        logger.info(
            f"Test database created successfully: {TestConfig.TEST_DATABASE_PATH}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to setup test database: {str(e)}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = setup_test_database()
    print(f"Database setup {'successful' if success else 'failed'}")
