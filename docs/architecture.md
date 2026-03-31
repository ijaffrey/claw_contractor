# CLAW Contractor Lead Management System
## High-Level Technical Architecture

### System Overview

The CLAW Contractor system is a Python-based lead management platform that automates the process of capturing, qualifying, and routing leads from Gmail to contractors. The system follows a modular, event-driven architecture with clear separation of concerns.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLAW CONTRACTOR SYSTEM                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐ │
│  │   Gmail API     │────│  Email Processor │────│ Lead Parser     │ │
│  │   Integration   │    │   (main.py)      │    │ & Adapter       │ │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘ │
│           │                       │                       │         │
│           ▼                       ▼                       ▼         │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐ │
│  │ Conversation    │────│   Qualification  │────│   Database      │ │
│  │ Manager         │    │   Engine         │    │   (Supabase)    │ │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘ │
│           │                       │                       │         │
│           ▼                       ▼                       ▼         │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐ │
│  │ Reply Generator │────│ Lead Handoff     │────│ Contractor      │ │
│  │ & Email Sender  │    │ Service          │    │ Notifications   │ │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘ │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                           WEB INTERFACE                            │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │ Flask Web App (patrick_web/app.py)                          │   │
│  │ - Lead Dashboard                                            │   │
│  │ - Handoff Management                                        │   │
│  │ - Business Onboarding                                       │   │
│  └───────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Email Processing Layer
- **Gmail Integration** (`gmail_listener.py`): Monitors Gmail for new leads via API polling
- **Lead Parser** (`lead_parser.py`): Extracts structured data from email content
- **Lead Adapter** (`lead_adapter.py`): Normalizes lead data to consistent format

#### 2. Conversation Management
- **Conversation Manager** (`conversation_manager.py`): Tracks multi-message exchanges
- **Reply Generator** (`reply_generator.py`): Creates contextual responses
- **Qualification Engine** (`qualification_engine.py`): Determines lead readiness

#### 3. Data Persistence
- **Database Layer** (`database.py`, `database_manager.py`): Supabase integration
- **Schema Management** (`conversation_schema.py`): Database structure definitions
- **Models** (`models/`): Data model definitions

#### 4. Lead Routing & Handoff
- **Lead Handoff Service** (`services/LeadHandoffService.py`): Manages contractor assignments
- **Notification System** (`contractor_notifier.py`, `notification_manager.py`): Alerts contractors
- **Customer Handoff** (`customer_handoff_messenger.py`): Transitions leads to contractors

#### 5. Web Interface
- **Flask Application** (`patrick_web/app.py`): Web dashboard
- **Routes** (`routes/`): API endpoints for web interface
- **Templates** (`templates/`): HTML email templates