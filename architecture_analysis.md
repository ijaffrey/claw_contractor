# Contractor AI Architecture Analysis

## Email Processing Pipeline

### Core Flow
1. **main.py** - Orchestrates the lead processing workflow
   - Initializes all modules (gmail_listener, lead_parser, lead_adapter, etc.)
   - Runs polling loop every 60 seconds
   - Coordinates between gmail listening, parsing, qualification, and notifications

2. **gmail_listener.py** - Handles Gmail OAuth2 and email retrieval
   - Authenticates via OAuth2 (token.json locally, GMAIL_TOKEN_JSON env var in production)
   - **Thread ID Source**: Extracts `thread_id` from Gmail message metadata (`message['threadId']`)
   - Returns email data including: id, thread_id, from, subject, date, body, snippet, attachments

3. **lead_parser.py** - Processes email content to create leads
   - Receives email data with thread_id from gmail_listener
   - Extracts lead information from email content
   - Creates Lead records in database

4. **reply_generator.py** - Claude API integration for responses
   - Uses Anthropic client with Config.ANTHROPIC_API_KEY
   - Model: "claude-sonnet-4-20250514" for replies, "claude-3-haiku-20240307" for analysis
   - Imports conversation_manager for thread context

## Thread ID Flow

**Origin**: Gmail API provides `threadId` in message metadata
**Usage Pattern**:
- gmail_listener extracts `message['threadId']` and includes it in email data dict
- lead_parser receives email data with thread_id
- conversation_manager uses thread_id to group related messages
- Thread ID is the key linking Gmail conversations to lead records

## Database Operations

### Current Schema (database.py)
- **Engine**: SQLAlchemy with SQLite (default) or PostgreSQL via DATABASE_URL
- **Session Management**: `get_db_session()` function used throughout
- **Models**:
  - `Lead`: Primary lead data (id, name, email, phone, company, status, etc.)
  - `NotificationLog`: Tracks notifications sent (email, SMS, webhook, slack)
- **Enums**: LeadStatus, NotificationType, NotificationStatus
- **Relationships**: Lead has many NotificationLog with cascade delete

### Missing Conversation Tables
- Current database.py shows NO conversation/thread tables
- conversation_manager.py imports database_manager but appears incomplete
- Need to add conversation tracking tables for thread management

## Claude API Integration Patterns

### reply_generator.py Implementation
```python
# Standard pattern:
client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    system=system_prompt,
    messages=[{"role": "user", "content": user_message}]
)
```

### Key Functions
- `build_system_prompt(business_profile)` - Creates branded system prompts
- `generate_reply()` - Main reply generation with conversation context
- `generate_followup_reply()` - Follow-up messages with conversation history
- Error handling with fallback templates

## Integration Points for Conversation Management

### 1. Database Layer
**Location**: database.py
**Needed**: Add conversation tables to track:
- thread_id (from Gmail)
- lead_id (foreign key)
- message history
- conversation state

### 2. Lead Creation
**Location**: lead_parser.py
**Integration**: Store thread_id when creating Lead records
**Pattern**: Use existing database session management

### 3. Reply Generation
**Location**: reply_generator.py
**Integration**: Already imports conversation_manager
**Pattern**: Load conversation history before calling Claude API

### 4. Gmail Processing
**Location**: gmail_listener.py
**Integration**: Already extracts thread_id from Gmail
**Pattern**: Pass thread_id through email processing pipeline

### 5. Main Orchestration
**Location**: main.py
**Integration**: Add conversation_manager to initialization
**Pattern**: Include conversation context in lead processing flow

## Current Conversation Management State

**conversation_manager.py**: Incomplete implementation
- Has DatabaseManager import
- Methods for loading conversation history by lead_id
- References undefined functions: `get_conversation_history()`, `get_lead_by_thread_id()`

**conversation_schema.py**: Exists but content unknown

## Recommendations

1. **Thread ID is already extracted** - Gmail listener provides this
2. **Database patterns are established** - Use existing SQLAlchemy session management
3. **Claude integration is mature** - Reuse existing Anthropic client pattern
4. **Missing pieces**: Conversation tables in database and proper conversation_manager implementation

## Next Steps for Implementation

1. Read conversation_schema.py to understand existing conversation structure
2. Add conversation tables to database.py using existing patterns
3. Complete conversation_manager.py implementation
4. Integrate conversation loading into reply_generator.py flow
5. Update lead_parser.py to store thread_id with leads