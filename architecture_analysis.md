# Contractor AI Architecture Analysis

## Overview
The Contractor AI system processes emails from Gmail, parses them for leads, generates AI responses, and manages conversation threads. The system uses SQLAlchemy for database operations, Gmail API for email handling, and Claude API for response generation.

## Email Processing Pipeline
Based on code analysis:

1. **gmail_listener.py** - Gmail OAuth2 authentication and email fetching
   - Extracts thread_id from Gmail API: `message['threadId']`
   - Returns email data with id, thread_id, from, subject, date, body, snippet
   - Handles OAuth token refresh and environment variable configuration

2. **lead_parser.py** - Email content parsing and lead extraction
   - Processes email data from gmail_listener
   - Creates Lead records in database

3. **reply_generator.py** - AI response generation using Claude API
   - Integrates with Claude for intelligent responses
   - Pattern to be reused for conversation management

4. **main.py** - System orchestration
   - Imports and coordinates all modules
   - Contains LeadManagementSystem class with conversation_manager integration
   - Includes gmail, parser, adapter, db, detector, notifier, reply_gen modules

## Database Schema
From database.py analysis:

### Lead Model
- id (Integer, primary key)
- name (String 255, not null)
- email (String 255, not null, indexed)
- phone (String 50, optional)
- company (String 255, optional)
- source (String 100, optional)
- status (Enum: NEW, CONTACTED, QUALIFIED, CONVERTED, LOST)
- notes (Text, optional)
- score (Integer, default 0)
- created_at/updated_at (DateTime)
- is_active (Boolean, default True)

### NotificationLog Model
- id (Integer, primary key)
- lead_id (Foreign key to leads.id)
- type (Enum: EMAIL, SMS, WEBHOOK, SLACK)
- status (Enum: PENDING, SENT, FAILED, DELIVERED)
- message, recipient, error_message (Text/String)
- attempts (Integer, default 0)
- timestamp, sent_at, delivered_at (DateTime)
- extra_data (Text, JSON string)

### Database Operations
- Uses get_db_session() pattern for connections
- SQLAlchemy with relationship mapping
- Lead.to_dict() and NotificationLog.to_dict() for serialization
- Migration support with _run_custom_migrations()

## Thread ID Flow
- **Origin**: Gmail API provides `message['threadId']`
- **Extraction**: gmail_listener.py line 270: `'thread_id': message['threadId']`
- **Usage**: Thread ID tracks email conversation threads for context
- **Current Gap**: No persistent thread storage in database schema

## Integration Points
1. **Gmail → Lead Parser**: Email data passed from gmail_listener to lead_parser
2. **Lead Parser → Database**: Lead records created via database.py models
3. **Database → Reply Generator**: Lead context retrieved for response generation
4. **Reply Generator → Gmail**: Responses sent back through Gmail API
5. **Conversation Manager**: New component for thread state management

## Claude API Pattern (from main.py)
- reply_generator module handles Claude integration
- Pattern shows modular approach for AI interactions
- Can be extended for conversation management context

## Current Limitations for Conversation Management
1. No thread_id field in database Lead model
2. No conversation history storage
3. No message sequence tracking
4. Reply generator likely stateless (needs verification)

## Recommended Integration Approach
1. Add conversation table linking to leads via thread_id
2. Store message history with sequence numbers
3. Extend reply_generator pattern for context-aware responses
4. Use existing get_db_session() pattern for new operations