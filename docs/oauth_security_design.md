# OAuth Token Security Design

## Overview
This document outlines the security design for storing OAuth tokens in Supabase, including encryption, access controls, and data retention policies.

## Table Structure

### oauth_tokens Table
The `oauth_tokens` table stores encrypted OAuth credentials with the following security features:

**Core Fields:**
- `id`: UUID primary key
- `user_email`: User identifier (VARCHAR(255))
- `service_provider`: OAuth provider (default: 'gmail')
- `client_id`: OAuth client identifier
- `token_type`: Enum (access_token, refresh_token, id_token)
- `encrypted_token`: AES encrypted token data
- `token_hash`: SHA-256 hash for quick lookups
- `scope`: OAuth scopes granted
- `expires_at`: Token expiration timestamp
- `status`: Enum (active, expired, revoked, invalid)

**Security & Audit Fields:**
- `last_used_at`: Last usage timestamp
- `usage_count`: Number of API calls made
- `ip_address`: Origin IP address
- `user_agent`: Client user agent
- `auto_delete_at`: Automatic cleanup timestamp

## Security Considerations

### Encryption at Rest
- **Algorithm**: AES encryption using PostgreSQL's pgcrypto extension
- **Key Management**: Encryption keys stored separately from database
- **Token Hashing**: SHA-256 hashes for token validation without decryption
- **No Plaintext Storage**: Tokens never stored in plaintext

### Access Control
- **Row Level Security (RLS)**: Enabled on oauth_tokens table
- **User Isolation**: Users can only access their own tokens
- **Service Account Access**: System processes can access all tokens with proper credentials
- **Unique Constraints**: Prevents duplicate active tokens per user/service/type

### Performance Optimization
- **Indexes**: Optimized for user/service lookups, token validation, and cleanup
- **Hash-based Lookups**: Fast token validation using SHA-256 hashes
- **Partial Indexes**: Conditional indexes for expired/auto-delete scenarios

## Data Retention Policy

### Automatic Cleanup
- **Expired Tokens**: Automatically deleted after expiration
- **Revoked Tokens**: Deleted 30 days after revocation
- **Usage-based Retention**: Tokens marked for deletion based on last usage
- **Scheduled Cleanup**: Database function runs periodically to remove old tokens

### Manual Operations
- **User Revocation**: Function to revoke all tokens for a user
- **Bulk Cleanup**: Administrative functions for maintenance
- **Audit Trail**: All operations logged in audit_log table

## Compliance

### Data Protection
- **GDPR Compliance**: User data can be completely removed
- **Minimal Data**: Only necessary OAuth data stored
- **Audit Logging**: All access and modifications logged
- **Data Anonymization**: Personal data separated from tokens where possible

### Security Standards
- **OAuth 2.0 Compliance**: Follows RFC 6749 security recommendations
- **Token Lifecycle Management**: Proper handling of token expiration and refresh
- **Secure Defaults**: Conservative security settings by default
- **Regular Rotation**: Supports token refresh patterns

## Implementation Notes

### Database Functions
- `encrypt_oauth_token()`: Encrypts tokens before storage
- `decrypt_oauth_token()`: Decrypts tokens for use (restricted access)
- `generate_token_hash()`: Creates SHA-256 hash for lookups
- `cleanup_expired_oauth_tokens()`: Scheduled cleanup function
- `revoke_user_oauth_tokens()`: Revokes all user tokens
- `update_token_usage()`: Updates usage statistics

### Monitoring View
- `oauth_tokens_monitor`: Non-sensitive view for monitoring token status
- **No Token Data**: View excludes encrypted tokens and hashes
- **Status Tracking**: Shows effective token status including expiration
- **Usage Analytics**: Provides usage statistics for monitoring

## Security Review Checklist

- [x] Tokens encrypted at rest using AES
- [x] No plaintext token storage
- [x] Row Level Security enabled
- [x] Unique constraints prevent duplicates
- [x] Automatic cleanup of expired tokens
- [x] Audit logging for all operations
- [x] User isolation enforced
- [x] Performance indexes optimized
- [x] Data retention policy defined
- [x] GDPR compliance considerations
