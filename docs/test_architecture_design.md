# Test Architecture Design for CLAW Contractor System

## High-Level Test Architecture

The test architecture follows a comprehensive multi-layered approach designed to ensure system reliability, performance, and maintainability.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TEST ARCHITECTURE LAYERS                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐ │
│  │   E2E Tests     │────│  Integration     │────│  Unit Tests     │ │
│  │   (Pytest)      │    │  Tests (Pytest) │    │  (Pytest)       │ │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘ │
│           │                       │                       │         │
│           ▼                       ▼                       ▼         │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐ │
│  │ Performance     │────│   Security       │────│  Load Tests     │ │
│  │ Tests (Locust)  │    │   Tests          │    │  (Artillery)    │ │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘ │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                      SUPPORTING INFRASTRUCTURE                      │
├─────────────────────────────────────────────────────────────────────┤
│  • Test Database (Supabase)  • Mock Services  • CI/CD Pipeline      │
│  • Test Data Factory         • Fixtures       • Coverage Reports     │
│  • Logging & Metrics         • Environment    • Quality Gates       │
└─────────────────────────────────────────────────────────────────────┘
```

## Technology Stack Recommendations

### Core Testing Technologies
- **pytest 7.4+**: Primary testing framework with async support
- **pytest-asyncio**: Async test execution
- **pytest-mock**: Advanced mocking capabilities
- **pytest-cov**: Code coverage analysis (target: 85%)
- **factory-boy**: Test data generation

### Integration & Performance Testing
- **requests-mock**: HTTP API mocking for Gmail/Anthropic APIs
- **unittest.mock**: Python object mocking
- **locust**: Performance and load testing framework
- **pytest-benchmark**: Micro-benchmarking for critical paths

### Quality Assurance Tools
- **black**: Code formatting enforcement
- **flake8**: Linting and style validation
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning

## Integration Points Testing

### Critical Integration Areas
1. **Gmail API Integration**
   - OAuth 2.0 authentication flow validation
   - Email parsing accuracy (>95% target)
   - Rate limiting and error handling
   - Webhook processing verification

2. **Database Integration**
   - Connection pooling verification
   - Transaction integrity testing
   - Data consistency across concurrent operations
   - Migration and schema validation

3. **Email Delivery Integration**
   - SMTP service connectivity testing
   - Template rendering accuracy validation
   - Delivery confirmation tracking
   - Bounce and failure handling scenarios

## Performance Requirements

### Performance Benchmarks

#### Email Processing Performance Targets
- **Throughput**: Process 100 emails/minute sustained
- **Memory Usage**: < 512MB peak memory consumption
- **Response Time**: < 5 seconds per email processing
- **Daily Capacity**: Handle 1,000+ leads per day

#### Database Performance Targets
- **Query Response**: < 200ms for standard lead lookups
- **Write Operations**: < 100ms for lead data storage
- **Concurrent Users**: Support 50 simultaneous users
- **Data Volume**: Efficiently handle 100,000+ lead records

#### API Performance Targets
- **Gmail API**: < 2 seconds for email retrieval operations
- **Anthropic API**: < 3 seconds for response generation
- **Email Delivery**: < 1 second for outbound email processing

## Security Considerations

### Security Test Categories

#### Authentication & Authorization Testing
- **OAuth 2.0 Flow Validation**: Complete authentication workflow testing
- **JWT Token Integrity**: Token generation, validation, and expiration
- **Session Management**: Secure session handling and cleanup
- **Role-Based Access Control**: Contractor data isolation verification

#### Data Protection Testing
- **PII Encryption**: Lead contact information encryption validation
- **Database Security**: Connection encryption and access control
- **API Endpoint Security**: Input validation and injection prevention
- **Audit Logging**: Comprehensive activity tracking verification

This architecture design provides comprehensive testing coverage for the CLAW Contractor system, ensuring reliability, performance, and security at all levels.

## System Components

### Core Application Layer
- **Main Coordinator** (`main.py`): Orchestrates the entire lead processing workflow with LeadManagementSystem class
- **Gmail Listener** (`gmail_listener.py`): Monitors Gmail inbox using OAuth2 authentication and Gmail API
- **Lead Parser** (`lead_parser.py`): Extracts structured data from lead emails using Claude API
- **Lead Adapter** (`lead_adapter.py`): Normalizes lead data into consistent format
- **Database Manager** (`database_manager.py`): Handles all database operations using SQLAlchemy ORM
- **Qualified Lead Detector** (`qualified_lead_detector.py`): Analyzes lead qualification status
- **Contractor Notifier** (`contractor_notifier.py`): Sends notifications to matched contractors
- **Reply Generator** (`reply_generator.py`): Generates and sends qualifying questions
- **Conversation Manager** (`conversation_manager.py`): Routes replies and manages lead state transitions

### Data Layer
- **Database Backend**: SQLAlchemy with configurable database URL (SQLite for testing)
- **Gmail API**: External email service integration with OAuth2 token management
- **Configuration Management**: Environment-specific settings via `config.py` and `test_env_config.py`
- **Models**: Database schema defined in `database.py` with User, Transaction, and Account entities

### Test Infrastructure
- **Test Environment Config** (`test_env_config.py`): Test-specific configuration and environment variables
- **Test Data Generation** (`test_data/`): Synthetic test data creation with privacy controls
- **Import Validation Scripts**: Verify module dependencies and imports
- **Mock Services**: Simulated external services for Gmail and Claude APIs
- **Logging Infrastructure**: Structured logging with dedicated test log files

## Data Flow Architecture

### Primary Lead Processing Flow
1. **Email Ingestion**: Gmail Listener authenticates via OAuth2 and monitors inbox
2. **Lead Classification**: Main coordinator determines if email is new lead or conversation reply
3. **Lead Extraction**: Lead Parser processes email content using Claude API
4. **Data Normalization**: Lead Adapter normalizes parsed data into consistent format
5. **Data Persistence**: Database Manager stores lead information using SQLAlchemy
6. **Qualification Analysis**: Qualified Lead Detector analyzes lead completeness
7. **Reply Generation**: Reply Generator creates qualifying questions and sends via Gmail
8. **Conversation Management**: Conversation Manager tracks ongoing conversations
9. **Contractor Matching**: System identifies suitable contractors based on lead criteria
10. **Notification Dispatch**: Contractor Notifier sends alerts to matched contractors

## Integration Points

### External Integrations
- **Gmail API**: OAuth2 authentication, email monitoring, reply sending with production token management
- **Claude API (Anthropic)**: Lead parsing and data extraction with API key security
- **Database**: SQLAlchemy ORM with SQLite (test) and PostgreSQL (production) backends

### Internal Module Integrations
- **Main → Gmail Listener**: Initiates email monitoring and authentication flow
- **Gmail Listener → Lead Parser**: Passes raw email data for Claude API processing
- **Lead Parser → Lead Adapter**: Provides parsed data for normalization
- **Lead Adapter → Database Manager**: Submits normalized lead data for storage
- **Database Manager → Qualified Lead Detector**: Provides lead data for qualification analysis
- **Qualified Lead Detector → Reply Generator**: Triggers qualifying question generation
- **Reply Generator → Gmail Listener**: Sends replies via authenticated Gmail service
- **Conversation Manager ↔ Database Manager**: Manages conversation state and progression

## Security Considerations

### Authentication & Authorization
- **Gmail OAuth2**: Production uses GMAIL_TOKEN_JSON environment variable, test uses limited scope
- **Claude API**: Secure API key management with environment variable isolation
- **Database Security**: SQLAlchemy connection security with test/production credential separation

### Data Protection
- **Lead Data Privacy**: Customer PII handling with test data anonymization
- **Test Environment Isolation**: Complete separation from production data and credentials
- **Audit Logging**: Comprehensive activity tracking with structured log format

## Scalability Requirements

### Performance Targets (Test Environment)
- **Email Processing**: Up to 1000 leads per hour
- **Database Operations**: < 1 second response time for standard queries
- **End-to-End Processing**: < 30 seconds from email receipt to contractor notification

### Resource Management
- **Database Connections**: SQLAlchemy connection pooling with configurable pool size
- **API Rate Limiting**: Respect Gmail and Claude API quotas
- **Memory Management**: Efficient handling of email content and parsed data
