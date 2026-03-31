# Infrastructure Provisioning Plan

## Overview
This document outlines the infrastructure setup and provisioning strategy for the Lead Management System.

## Infrastructure Architecture

### Core Components
1. **Application Layer** - Python application with Flask/FastAPI
2. **Database Layer** - Supabase (PostgreSQL) for production, SQLite for development
3. **External APIs** - Gmail API, Anthropic Claude API
4. **Monitoring & Logging** - Centralized logging and metrics collection

## Environment-Specific Infrastructure

### Development Environment
- Python 3.8+ Virtual Environment
- SQLite Database (local)
- File-based Logging
- Mock External Services (optional)
- Hot Reload Development Server

### Production Environment
- High Availability Application
- Supabase Production Database
- Distributed Logging & Metrics
- Rate Limiting & Throttling
- Backup & Recovery Systems

## Database Infrastructure

### Supabase Setup
```sql
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    subject TEXT,
    content TEXT,
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    message_type VARCHAR(50),
    content TEXT,
    sender VARCHAR(255),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE contractors (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Database Configuration
- Connection Pooling: Max 20 connections
- SSL: Required for all connections
- Backup: Daily automated backups
- Monitoring: Query performance metrics

## External API Infrastructure

### Gmail API Setup
1. Google Cloud Console Project
   - APIs Enabled: Gmail API, Google Auth Library
   - OAuth 2.0 Credentials configured

2. Rate Limits
   - Gmail API: 250 quota units per user per 100 seconds
   - Exponential backoff for rate limit handling

### Anthropic Claude API
1. API Configuration
   - Model: Claude-3 (latest stable version)
   - Rate Limiting: 5,000 requests per minute
   - Timeout: 30 seconds per request

## Security Infrastructure

### API Key Management
```bash
# Environment Variables (Production)
ANTHROPIC_API_KEY=<encrypted_key>
GMAIL_CREDENTIALS=<encrypted_json>
SUPABASE_KEY=<encrypted_key>
DATABASE_URL=<encrypted_connection_string>
```

### Access Controls
1. Network Security
   - VPC/Private networks
   - Firewall rules (restrictive by default)
   - HTTPS/TLS 1.3 for all communications

2. Authentication & Authorization
   - OAuth2 for Gmail API
   - API key rotation (90-day cycle)
   - Principle of least privilege

## Monitoring & Logging

### Logging Strategy
- Structured JSON logging
- Log rotation (10MB files, 5 backups)
- Centralized log aggregation
- Different log levels per environment

### Monitoring Metrics
1. Application Metrics
   - Request/response times
   - Error rates
   - Email processing volume

2. System Metrics
   - CPU/Memory utilization
   - Disk usage
   - Process health

## Deployment Infrastructure

### Container Strategy
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

## Health Checks & Monitoring

### Application Health Endpoints
```python
@app.route('/health')
def health_check():
    checks = {
        'database': check_database_connection(),
        'gmail_api': check_gmail_api_status(),
        'anthropic_api': check_anthropic_api_status()
    }
    overall_status = 'healthy' if all(checks.values()) else 'unhealthy'
    return {'status': overall_status, 'checks': checks}
```

## Cost Optimization

### Resource Planning
```yaml
Development:
  - Supabase Free Tier: $0
  - Gmail API: $0 (within limits)
  - Anthropic API: ~$50
  Total: ~$50/month

Production:
  - Supabase Pro: $25
  - Anthropic API: ~$200
  - Cloud Infrastructure: ~$100
  Total: ~$325/month
```