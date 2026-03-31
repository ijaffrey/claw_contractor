# Configuration Management Strategy

## Overview
This document defines the configuration management approach for the Lead Management System, ensuring secure, scalable, and maintainable configuration across all environments.

## Configuration Architecture

### Hierarchical Configuration
```
Configuration Priority (High to Low):
1. Environment Variables
2. .env file
3. Default values in config.py
4. System defaults
```

### Environment-Specific Configuration
- **Development**: Local .env file with development defaults
- **Staging**: Environment variables with staging endpoints
- **Production**: Encrypted environment variables with production services

## Configuration Categories

### 1. Application Configuration
```python
# Application Settings
APP_NAME = 'Lead Management System'
DEBUG = False
LOG_LEVEL = 'INFO'
POLL_INTERVAL = 60  # seconds
MAX_RETRIES = 3
```

### 2. Database Configuration
```python
# Database Settings
DATABASE_URL = 'postgresql://user:pass@host:port/db'
SUPABASE_URL = 'https://your-project.supabase.co'
SUPABASE_KEY = 'your-supabase-key'
DB_POOL_SIZE = 20
DB_TIMEOUT = 30
```

### 3. Email Configuration
```python
# Gmail API Settings
GMAIL_CREDENTIALS_FILE = 'credentials.json'
GMAIL_TOKEN_FILE = 'token.json'
GMAIL_SCOPES = ['gmail.readonly', 'gmail.send']

# SMTP Settings (fallback)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USE_TLS = True
SMTP_USERNAME = 'user@gmail.com'
SMTP_PASSWORD = 'app_password'
```

### 4. API Configuration
```python
# Anthropic Claude API
ANTHROPIC_API_KEY = 'your-api-key'
ANTHROPIC_MODEL = 'claude-3-sonnet-20240229'
ANTHROPIC_MAX_TOKENS = 4096
ANTHROPIC_TIMEOUT = 30

# Rate Limiting
API_RATE_LIMIT = 100  # requests per minute
API_RETRY_DELAY = 1  # seconds
```

## Configuration Management Implementation

### Config Class Structure
```python
# Enhanced config.py structure
class BaseConfig:
    """Base configuration with common settings"""
    
    def __init__(self):
        self.load_environment()
        self.validate_config()
    
    def get_env(self, key: str, default: Any = None, required: bool = False) -> Any:
        """Get environment variable with validation"""
        value = os.getenv(key, default)
        if required and value is None:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def validate_config(self):
        """Validate configuration values"""
        required_vars = ['ANTHROPIC_API_KEY', 'DATABASE_URL']
        for var in required_vars:
            if not self.get_env(var):
                raise ValueError(f"Required configuration {var} is missing")

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    DATABASE_URL = 'sqlite:///dev_leads.db'
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = 'INFO'
```

### Environment Variable Management
```bash
# .env.example (Development Template)
# Application
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite:///dev_leads.db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# Gmail API
GMAIL_CREDENTIALS_FILE=credentials.json

# Anthropic API
ANTHROPIC_API_KEY=your-claude-api-key

# Email
CONTRACTOR_EMAIL=contractor@company.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Configuration Security

### Secrets Management
- Environment variables for sensitive data
- Encrypted storage for production secrets
- API key rotation procedures
- No hardcoded credentials in code

### Configuration Validation
```python
# Basic validation approach
def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    pattern = r'^https?://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})+(?:/.*)?$'
    return bool(re.match(pattern, url))
```

## Configuration Loading Strategy

### Dynamic Configuration Loading
```python
# Configuration loading priority
1. Load defaults from config.py
2. Override with .env file values
3. Override with environment variables
4. Validate all configuration
5. Apply environment-specific overrides
```

## Best Practices

1. **Environment Separation**: Different configurations for dev/staging/prod
2. **Security First**: Never commit secrets to version control
3. **Validation**: Always validate configuration on startup
4. **Documentation**: Keep configuration options well-documented
5. **Defaults**: Provide sensible defaults for non-sensitive settings