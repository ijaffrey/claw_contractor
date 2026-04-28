#!/usr/bin/env python3
"""Migration script to create user_tokens table"""

from database import Base, engine, UserToken


def create_user_tokens_table():
    """Create the user_tokens table"""
    try:
        # Create the table
        UserToken.__table__.create(engine, checkfirst=True)
        print("✓ user_tokens table created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating user_tokens table: {e}")
        return False


if __name__ == "__main__":
    success = create_user_tokens_table()
    exit(0 if success else 1)
