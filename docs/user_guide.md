# Lead Management System User Guide

## Overview
The Lead Management System is an automated solution for processing contractor leads from email inquiries. This guide covers system operation, monitoring, and maintenance procedures.

## Getting Started

### System Requirements
- Python 3.9+
- Gmail account with API access
- Supabase database connection
- SMTP server for email sending

### Initial Setup
1. **Environment Configuration**
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

2. **Database Initialization**
   ```bash
   python3 test_db_setup.py
   python3 seed_contractor.py
   ```

3. **System Validation**
   ```bash
   python3 test_health_check.py
   ```

## System Operation

### Starting the System
```bash
# Production mode
python3 main.py

# Dry run mode (no emails sent)
python3 main.py --dry-run

# Development mode with logging
python3 main.py --debug
```

### Monitoring System Status
The system provides real-time status information:
- **Console Output**: Live processing logs
- **Log Files**: Detailed operation logs in `logs/` directory
- **Health Reports**: System health status in JSON format

### Key System Indicators
- ✅ Gmail connection active
- ✅ Database connectivity confirmed
- ✅ SMTP server responsive
- ✅ Lead processing pipeline operational

## Lead Processing Workflow

### 1. Email Detection
- System polls Gmail every 60 seconds
- New emails are automatically detected
- Lead qualification begins immediately

### 2. Lead Qualification
- Email content parsed for lead information
- Qualifying questions sent to potential customer
- System tracks conversation state

### 3. Contractor Notification
- Qualified leads trigger contractor alerts
- Notification includes lead details and contact info
- Handoff process initiated

### 4. Conversation Management
- Multi-message conversations handled automatically
- Context preserved across email exchanges
- Appropriate responses generated based on content

## Administrative Functions

### Viewing System Logs
```bash
# View real-time system logs
tail -f logs/test_system.log

# Check database operations
tail -f logs/test_database.log

# Monitor notifications
tail -f logs/test_notifications.log
```

### Database Management
```bash
# View current leads
python3 -c "from database import get_all_leads; print(get_all_leads())"

# Reset database (caution: deletes all data)
python3 test_db_setup.py --reset
```

### Testing System Components
```bash
# Test email connectivity
python3 test_gmail_listener.py

# Test database operations
python3 test_database.py

# Test notification system
python3 test_notification_manager.py
```

## Configuration Management

### Environment Variables
Key configuration settings in `.env` file:
- `GMAIL_CREDENTIALS`: Gmail API credentials
- `SUPABASE_URL`: Database connection URL
- `SUPABASE_KEY`: Database access key
- `SMTP_SERVER`: Email server configuration

### System Settings
Modify `config.py` for operational parameters:
- Polling intervals
- Lead qualification criteria
- Notification templates
- Response generation settings

## Troubleshooting Common Issues

### Email Connection Problems
**Symptom**: Gmail polling failures
**Solution**:
1. Verify Gmail API credentials
2. Check network connectivity
3. Confirm API quotas not exceeded

### Database Connection Issues
**Symptom**: Database operation failures
**Solution**:
1. Verify Supabase credentials
2. Check database connectivity
3. Confirm table structure exists

### Notification Delivery Problems
**Symptom**: Contractors not receiving alerts
**Solution**:
1. Test SMTP server configuration
2. Verify contractor email addresses
3. Check spam folder delivery

### Performance Issues
**Symptom**: Slow response times
**Solution**:
1. Monitor system resource usage
2. Check database query performance
3. Review email processing volumes

## Maintenance Procedures

### Daily Operations
- Monitor system status dashboard
- Review processing logs for errors
- Verify lead qualification accuracy

### Weekly Maintenance
- Review system performance metrics
- Check database storage usage
- Update lead qualification criteria if needed

### Monthly Tasks
- Archive old log files
- Review and update contractor contact information
- Analyze lead conversion rates
- Update system documentation

## Support and Escalation

### Self-Service Resources
1. Check system health status
2. Review troubleshooting guide
3. Examine recent log entries
4. Run diagnostic tests

### When to Escalate
- Persistent system failures
- Database corruption issues
- Security-related concerns
- Performance degradation

### Emergency Procedures
For critical system failures:
1. Stop the main process
2. Preserve log files
3. Document error symptoms
4. Contact system administrator

## System Limits and Quotas

### Gmail API Limits
- 250 quota units per user per 100 seconds
- 1 billion quota units per day

### Database Limits
- Based on Supabase plan limits
- Monitor storage usage regularly

### Processing Capacity
- Designed for up to 1000 leads per day
- Can process 100 concurrent conversations

## Best Practices

### Operational Guidelines
- Monitor system regularly during business hours
- Keep configuration files secure and backed up
- Test changes in development environment first
- Maintain up-to-date documentation

### Security Considerations
- Protect API credentials
- Use secure connections for all communications
- Regularly rotate access keys
- Monitor for unauthorized access

### Performance Optimization
- Adjust polling intervals based on volume
- Archive old data regularly
- Monitor system resource usage
- Optimize database queries as needed
