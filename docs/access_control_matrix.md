# Access Control Matrix - Test Environment

**Last Updated:** December 2024  
**Environment:** Test/Development  
**Security Review:** Completed

## Overview

This document defines the access control matrix for the Lead Management System test environment. All permissions have been reviewed and configured according to the principle of least privilege.

## Role Definitions

### System Role
- **Description:** Automated system processes
- **Scope:** Full system access for operational functions
- **Authentication:** Service account with JWT tokens

### Test User Role
- **Description:** Human testers and developers
- **Scope:** Limited access for testing and development
- **Authentication:** Username/password with MFA

### Guest Role
- **Description:** Read-only access for demonstrations
- **Scope:** View-only permissions
- **Authentication:** Guest token (limited duration)

## Access Control Matrix

| Resource | System | Test User | Guest |
|----------|--------|-----------|-------|
| **Gmail API** | | | |
| - Read emails | ✓ | ✗ | ✗ |
| - Send emails | ✓ | ✗ | ✗ |
| - Manage labels | ✓ | ✗ | ✗ |
| **Database** | | | |
| - Read leads | ✓ | ✓ | ✗ |
| - Write leads | ✓ | ✗ | ✗ |
| - Delete records | ✓ | ✗ | ✗ |
| - Schema changes | ✓ | ✗ | ✗ |
| **Web Interface** | | | |
| - View dashboard | N/A | ✓ | ✓ |
| - Create entries | N/A | ✓ | ✗ |
| - Edit entries | N/A | ✓ | ✗ |
| - Delete entries | N/A | ✗ | ✗ |
| **Admin Functions** | | | |
| - System config | ✓ | ✗ | ✗ |
| - User management | ✓ | ✗ | ✗ |
| - Security settings | ✓ | ✗ | ✗ |
| - Logs access | ✓ | LIMITED | ✗ |

## Authentication Methods

### JWT Authentication
- **Used by:** System role
- **Token lifetime:** 30 minutes
- **Refresh policy:** Automatic
- **Algorithm:** HS256 with rotating keys

### Session-based Authentication
- **Used by:** Test User, Guest roles
- **Session timeout:** 30 minutes
- **Cookie security:** HttpOnly, Secure, SameSite
- **CSRF protection:** Enabled

## Network Access Controls

### Allowed IP Ranges
```
127.0.0.1/32     # Localhost
192.168.1.0/24   # Local development network
10.0.0.0/16      # Docker/container networks
```

### Port Restrictions
- **Web interface:** 8080 (local only)
- **API endpoints:** 8000 (restricted)
- **Database:** Local socket only

## Rate Limiting

| Endpoint | System | Test User | Guest |
|----------|--------|-----------|-------|
| Authentication | 1000/15min | 10/15min | 5/15min |
| API calls | 1000/15min | 100/15min | 10/15min |
| Web requests | N/A | 200/15min | 50/15min |

## Data Access Permissions

### PII Access
- **System:** Full access (encrypted storage)
- **Test User:** Masked data only
- **Guest:** No PII access

### Log Access
- **System:** All logs
- **Test User:** Application logs only
- **Guest:** No log access

## Implementation Details

### Configuration Files
- **Security config:** `infrastructure/security_config.py`
- **JWT settings:** Environment variables
- **Session config:** `config.py`

### Middleware
- **Authentication:** FastAPI dependency injection
- **Authorization:** Role-based decorators
- **Rate limiting:** Redis-backed counters

## Monitoring and Auditing

### Access Logging
- All authentication attempts logged
- Permission denials recorded
- Privilege escalation alerts
- Regular access pattern analysis

### Security Events
- Failed login attempts (3+ triggers alert)
- Unusual access patterns
- Permission boundary violations
- Token/session anomalies

## Security Hardening

### Database Security
- File permissions: 600 (owner only)
- Connection encryption: TLS 1.3
- Query logging: Enabled
- Backup encryption: AES-256

### Web Application
- HTTPS enforcement
- Security headers configured
- Input validation on all endpoints
- Output encoding for XSS prevention

## Emergency Procedures

### Access Revocation
1. Disable user account immediately
2. Invalidate all active sessions
3. Rotate JWT signing keys
4. Review access logs for suspicious activity

### Incident Response
1. Isolate affected systems
2. Preserve audit logs
3. Assess scope of compromise
4. Implement containment measures
5. Document all actions taken

## Compliance Notes

- **GDPR:** Right to deletion implemented
- **CCPA:** Consumer access rights configured
- **SOC 2:** Access controls documented
- **ISO 27001:** Security frameworks aligned

## Review Schedule

- **Weekly:** Access pattern analysis
- **Monthly:** Permission review
- **Quarterly:** Security assessment
- **Annually:** Full access control audit

---

**Next Review Date:** January 2025  
**Approved by:** Security Team  
**Document Version:** 1.0
