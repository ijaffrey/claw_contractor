# Troubleshooting Guide

## Overview
Quick solutions to common issues in the Lead Management System.

## Quick Diagnostics

### System Health Check
```bash
# Run comprehensive health check
python3 test_health_check.py

# Check specific components
python3 test_database.py
python3 test_gmail_listener.py
python3 test_email_sender.py
```

### Log Analysis
```bash
# Check recent system activity
tail -100 logs/test_system.log

# Monitor real-time logs
tail -f logs/test_system.log

# Search for errors
grep -i "error\|exception\|failed" logs/test_system.log
```

## Email System Issues

### Gmail Connection Failures
**Symptoms:** Authentication failed, quota exceeded, connection timeouts

**Solutions:**
1. Test Gmail authentication: `python3 test_gmail_listener.py`
2. Check API quotas in Google Cloud Console
3. Verify network connectivity: `ping gmail.googleapis.com`
4. Check firewall settings: `telnet smtp.gmail.com 587`

### Email Sending Problems
**Symptoms:** SMTP authentication failures, messages not delivered

**Solutions:**
1. Test email sending: `python3 test_email_sender.py`
2. Verify SMTP server address, port, and credentials
3. Check recipient spam folders
4. Review email content for spam triggers

## Database Issues

### Connection Failures
**Symptoms:** Unable to connect, timeout exceptions, authentication failures

**Solutions:**
1. Test connection: `python3 test_database.py`
2. Verify Supabase URL and API key in `.env`
3. Check network connectivity to Supabase
4. Reset database: `python3 test_db_setup.py --reset` (CAUTION: deletes data)

### Data Corruption
**Symptoms:** Inconsistent data, foreign key errors, unexpected results

**Solutions:**
1. Clean test data: `python3 test_data/data_cleaner.py`
2. Regenerate data: `python3 test_data/data_generator.py`
3. Validate integrity: `python3 test_basic_validation.py`

## Lead Processing Issues

### Lead Parser Failures
**Symptoms:** Email content not extracted, missing information, parsing exceptions

**Solutions:**
1. Test parser: `python3 test_lead_parser.py`
2. Check email structure and encoding
3. Verify HTML vs plain text handling
4. Update extraction patterns in `lead_parser.py`

### Qualification Problems
**Symptoms:** Incorrect lead scoring, qualification logic errors

**Solutions:**
1. Test qualification: `python3 test_qualified_lead_detector.py`
2. Review qualification rules in `qualification_engine.py`
3. Verify scoring algorithms and thresholds

## Notification System Issues

### Missing Contractor Notifications
**Symptoms:** Contractors not receiving alerts, delivery failures

**Solutions:**
1. Test notifications: `python3 test_notification_manager.py`
2. Verify contractor email addresses
3. Check SMTP settings for notifications
4. Review notification logs: `tail -f logs/test_notifications.log`

### Logging Issues
**Symptoms:** Missing records, log write failures

**Solutions:**
1. Test logger: `python3 test_notification_logger.py`
2. Check log file write permissions
3. Verify disk space availability

## Performance Issues

### Slow Response Times
**Symptoms:** Processing delays, timeouts, high resource usage

**Solutions:**
1. Monitor resources: `top` or `htop`
2. Check process usage: `ps aux | grep python`
3. Review database query performance
4. Optimize code bottlenecks

### Memory Issues
**Symptoms:** Increasing memory usage, out of memory errors

**Solutions:**
1. Monitor memory: `watch -n 1 'ps aux | grep python'`
2. Check for unclosed connections
3. Review large object handling
4. Implement proper cleanup

## Environment Issues

### Configuration Problems
**Symptoms:** Environment variable errors, missing config files

**Solutions:**
1. Validate environment: `python3 test_env_config.py`
2. Check requirements: `python3 test_environment_requirements.py`
3. Reset configuration: `cp env.example .env`

### Dependency Issues
**Symptoms:** Import errors, module not found, version conflicts

**Solutions:**
1. Check dependencies: `pip3 list` and `pip3 check`
2. Reinstall: `pip3 install --break-system-packages -r requirements.txt`
3. Verify Python version compatibility

## Emergency Procedures

### System Recovery
1. Stop processes: `pkill -f main.py`
2. Backup logs: `cp -r logs logs_backup_$(date +%Y%m%d_%H%M%S)`
3. Reset system:
   ```bash
   python3 test_db_setup.py
   python3 seed_contractor.py
   python3 test_health_check.py
   ```

### When to Escalate
- Persistent failures after troubleshooting
- Data corruption or loss
- Security incidents
- Performance degradation

### Information to Provide
- Error messages and stack traces
- Log file excerpts
- System configuration details
- Steps to reproduce
- Impact assessment
