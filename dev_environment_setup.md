# Development Environment Setup Plan

## Environment Requirements

### Runtime Environment
- **Python**: 3.8+ (Current codebase uses Python 3.14 features)
- **Operating System**: Cross-platform (Linux, macOS, Windows)
- **Memory**: Minimum 2GB RAM, Recommended 4GB+
- **Storage**: Minimum 1GB free space

### Core Dependencies
```
# Gmail API Integration
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.116.0

# Database (Supabase)
supabase==2.28.2
websockets>=15.0,<16.0

# AI/ML (Anthropic Claude)
anthropic==0.84.0

# Configuration Management
python-dotenv==1.0.1
python-dateutil==2.8.2
```

### Development Tools
- **Code Editor**: VS Code with Python extension
- **Version Control**: Git
- **Package Manager**: pip3
- **Virtual Environment**: venv or conda
- **Testing**: pytest (for future test implementation)

## Infrastructure Requirements

### External Services
1. **Gmail API**
   - Google Cloud Console project
   - Gmail API enabled
   - OAuth2 credentials configured
   - Application-specific passwords

2. **Supabase Database**
   - Supabase project setup
   - Database URL and API keys
   - Required tables: leads, conversations, contractors, notifications

3. **Anthropic Claude API**
   - API key for text generation
   - Rate limiting considerations

### Local Infrastructure
- **Database**: SQLite for local development/testing
- **Logging**: File-based logging with rotation
- **Configuration**: Environment-based config management

## Configuration Management Strategy

### Environment Variables
Using `.env` file pattern with the following structure:

```bash
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# API Keys
ANTHROPIC_API_KEY=your-claude-api-key

# Application Configuration
CONTRACTOR_EMAIL=contractor@company.com
DEBUG=false
LOG_LEVEL=INFO
```

### Configuration Management Features
- Environment-specific configurations
- Sensitive data protection
- Default value fallbacks
- Type validation and conversion
- Configuration validation on startup

## Development Tools List

### Core Development
1. **Python 3.8+**
   - Virtual environment (venv/conda)
   - pip3 package manager

2. **Code Editor Setup**
   - VS Code with Python extension
   - Pylint for code quality
   - Black for code formatting
   - Python debugger configuration

3. **Version Control**
   - Git with proper .gitignore
   - Branch protection for main
   - Commit message conventions

### Quality Assurance
1. **Testing Framework**
   - pytest for unit testing
   - Coverage reporting
   - Integration test support

2. **Code Quality**
   - Pylint/Flake8 for linting
   - Black for formatting
   - Type hints with mypy
   - Pre-commit hooks

3. **Security**
   - Dependency vulnerability scanning
   - Environment variable validation
   - API key rotation procedures

### Monitoring & Debugging
1. **Logging**
   - Structured logging with JSON format
   - Log rotation and archival
   - Different log levels per environment

2. **Monitoring**
   - Health check endpoints
   - Performance metrics
   - Error tracking and alerting

3. **Debugging**
   - Python debugger (pdb/VS Code)
   - Request/response logging
   - Database query logging

## Environment Setup Checklist

### Initial Setup
- [ ] Install Python 3.8+
- [ ] Create virtual environment
- [ ] Install dependencies from requirements.txt
- [ ] Copy .env.example to .env
- [ ] Configure environment variables

### Service Setup
- [ ] Create Google Cloud Console project
- [ ] Enable Gmail API
- [ ] Generate OAuth2 credentials
- [ ] Set up Supabase project
- [ ] Create database tables
- [ ] Obtain Anthropic API key

### Development Environment
- [ ] Configure code editor
- [ ] Set up Git repository
- [ ] Install development tools
- [ ] Configure debugging
- [ ] Set up testing framework

### Validation
- [ ] Run health checks
- [ ] Test database connectivity
- [ ] Verify Gmail API connection
- [ ] Test email sending/receiving
- [ ] Validate Claude API integration

### Security
- [ ] Secure API keys
- [ ] Configure access controls
- [ ] Set up monitoring/alerting
- [ ] Document incident response
- [ ] Regular security updates

## Deployment Considerations

### Local Development
- SQLite database for development
- File-based logging
- Mock external services for testing
- Hot reload for development

### Staging Environment
- PostgreSQL database
- Centralized logging
- Real external services
- Performance monitoring

### Production Environment
- High availability database
- Distributed logging
- Rate limiting and throttling
- Comprehensive monitoring
- Backup and recovery procedures

## Infrastructure Provisioning Plan

### Cloud Infrastructure
1. **Database (Supabase)**
   - Project setup and configuration
   - Table schema creation
   - Access control setup
   - Backup configuration

2. **Monitoring & Logging**
   - Centralized log aggregation
   - Performance metrics collection
   - Alert configuration
   - Dashboard setup

3. **Security**
   - API key management
   - Access control policies
   - Network security
   - Data encryption

### Automation
- Infrastructure as Code (IaC)
- Automated deployments
- Configuration management
- Monitoring setup automation