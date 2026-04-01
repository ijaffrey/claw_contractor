# main.py Structure Analysis

## File Metrics
- Total lines: 513
- File type: Flask application with LeadManagementSystem class

## Flask Routes Analysis
- Routes at line 379: `@app.route('/auth/google')` - OAuth initiation route
- Routes at line 435: `@app.route('/auth/google/callback')` - OAuth callback route
- Complete route inventory:
  - `/auth/google` (line 379): Initiates Google OAuth flow for Gmail authentication
  - `/auth/google/callback` (line 435): Handles OAuth callback and token exchange

## Dependencies and Imports
### Core Application Modules:
- `gmail_listener` - Gmail API integration
- `lead_parser` - Email content parsing
- `lead_adapter` - Lead data normalization
- `database_manager` - Database operations
- `qualified_lead_detector` - Lead qualification analysis
- `contractor_notifier` - Contractor notification system
- `reply_generator` - Automated email responses
- `conversation_manager` - Conversation state management

### Flask Dependencies (line 370):
- `from flask import Flask, request, redirect, session, url_for`
- Flask app initialization at line 376: `app = Flask(__name__)`

### Standard Library Imports:
- `argparse` - Command line argument parsing
- `logging` - Structured logging system
- `signal`, `sys`, `time` - System utilities
- `typing.Dict, Any, List` - Type hints
- `datetime` - Date/time handling

## End-of-file Structure
- OAuth callback handler with token exchange and credential saving
- Command line argument parsing with `--dry-run` and `--oauth-server` flags
- Main execution block that either runs OAuth server or LeadManagementSystem
- OAuth server runs on localhost:5000 for Gmail authentication

## Flask App Configuration
- Flask app created at line 376
- Two OAuth-related routes for Google authentication workflow
- OAuth server mode available via `--oauth-server` command line flag
- Integrates with LeadManagementSystem class for lead processing workflow
- Uses session management for OAuth state tracking
- Saves credentials to `token.json` file for local development

## Architecture Overview
- Primary structure: LeadManagementSystem class-based application
- Flask routes serve as OAuth authentication endpoints only
- Main workflow: Email monitoring → Lead parsing → Qualification → Contractor notification
- Supports dry-run mode for testing without actual operations
- Modular design with separate modules for each workflow step