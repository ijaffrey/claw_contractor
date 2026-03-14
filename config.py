"""
Configuration loader for OpenClaw Trade Assistant
Loads all environment variables and validates required settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables"""

    # Gmail API Configuration
    GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID')
    GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET')
    GMAIL_USER_EMAIL = os.getenv('GMAIL_USER_EMAIL')

    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    # Anthropic Claude API Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

    # Application Settings
    POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', 30))

    # Gmail API Scopes
    GMAIL_SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.send'
    ]

    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_vars = {
            'GMAIL_CLIENT_ID': cls.GMAIL_CLIENT_ID,
            'GMAIL_CLIENT_SECRET': cls.GMAIL_CLIENT_SECRET,
            'GMAIL_USER_EMAIL': cls.GMAIL_USER_EMAIL,
            'SUPABASE_URL': cls.SUPABASE_URL,
            'SUPABASE_KEY': cls.SUPABASE_KEY,
            'ANTHROPIC_API_KEY': cls.ANTHROPIC_API_KEY,
        }

        missing = [key for key, value in required_vars.items() if not value]

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file and ensure all variables from .env.example are set."
            )

        return True


# Validate configuration on import
if __name__ != '__main__':
    try:
        Config.validate()
        print("✓ Configuration loaded successfully")
    except ValueError as e:
        print(f"⚠ Configuration warning: {e}")
