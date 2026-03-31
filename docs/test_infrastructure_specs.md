# Test Infrastructure Technical Specifications

## Railway Deployment Configuration

### Environment Setup
```yaml
runtime: python3.11
start_command: python3 main.py
health_check: /health
port: 8080
build_command: pip3 install --break-system-packages -r requirements.txt
```

### Required Environment Variables
```bash
# Email Service Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=${TEST_EMAIL_USERNAME}
MAIL_PASSWORD=${TEST_EMAIL_APP_PASSWORD}

# Database Configuration
SUPABASE_URL=${TEST_SUPABASE_URL}
SUPABASE_ANON_KEY=${TEST_SUPABASE_ANON_KEY}
SUPABASE_SERVICE_KEY=${TEST_SUPABASE_SERVICE_KEY}

# AI Service Configuration
ANTHROPIC_API_KEY=${TEST_ANTHROPIC_KEY}

# Test Environment Settings
TEST_MODE=true
LOG_LEVEL=DEBUG
PYTHON_ENV=test
```

## Supabase Database Schema

### Required Tables
```sql
-- conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    thread_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- leads table
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(100),
    content TEXT,
    parsed_data JSONB,
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Test Data Seeding
```python
# Sample test data insertion
test_customers = [
    {'email': 'test1@example.com', 'name': 'Test Customer 1', 'phone': '555-0101'},
    {'email': 'test2@example.com', 'name': 'Test Customer 2', 'phone': '555-0102'}
]

test_leads = [
    {'source': 'email', 'content': 'Need roofing work', 'status': 'new'},
    {'source': 'email', 'content': 'Kitchen renovation', 'status': 'qualified'}
]
```

## Resource Allocation

### Compute Resources
- **CPU**: 1 vCPU (burstable to 2 vCPU under load)
- **Memory**: 512MB RAM (expandable to 1GB if needed)
- **Storage**: 1GB persistent storage
- **Network**: 100GB monthly bandwidth
- **Uptime**: 99.9% availability target

### Database Resources
- **Engine**: PostgreSQL 15.x
- **Storage**: 500MB allocated (100MB for test data)
- **Connections**: 100 max concurrent connections
- **Backup**: Hourly snapshots, 24-hour retention
- **Replication**: Single instance (test environment)

## Monitoring Configuration

### Application Metrics
```python
metrics_config = {
    'response_time_threshold': 2000,  # milliseconds
    'error_rate_threshold': 5,        # percentage
    'memory_usage_threshold': 80,     # percentage
    'cpu_usage_threshold': 75         # percentage
}
```

### Health Check Endpoints
```python
# /health - Basic health check
# /health/db - Database connectivity
# /health/external - External service status
# /metrics - Prometheus metrics
```

### Logging Configuration
```python
logging_config = {
    'level': 'DEBUG',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': ['console', 'file'],
    'max_file_size': '10MB',
    'backup_count': 5
}
```

---
**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Owner**: DevOps Team
