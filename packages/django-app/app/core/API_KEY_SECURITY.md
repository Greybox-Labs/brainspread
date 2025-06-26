# API Key Security Documentation

This document provides comprehensive information about the secure API key storage system implemented in this Django application.

## Overview

The API key system provides multiple layers of security for storing and managing user API keys, including field-level encryption, user-specific salting, secure key derivation, and comprehensive audit logging.

## Security Features

### 1. Field-Level Encryption

API keys can be stored with field-level encryption using the Fernet symmetric encryption algorithm (AES 128 in CBC mode):

```python
# Encrypt a key for storage
api_key.encrypt_key("user-api-key-value")

# Decrypt a key for use
decrypted_key = api_key.decrypt_key()
```

**Security Properties:**
- Uses cryptographically secure Fernet encryption
- Each user has a unique encryption key derived from their salt
- Encrypted keys cannot be retrieved without the master secret

### 2. User-Specific Salting

Every API key gets a unique 32-byte salt that is specific to the user:

```python
# Salt is automatically generated on save
api_key = APIKey.objects.create(user=user, name="my-key")
print(api_key.salt)  # Base64 encoded 32-byte salt
```

**Security Properties:**
- Prevents rainbow table attacks
- Ensures identical keys have different encrypted/hashed values across users
- Salt is cryptographically random (using `secrets.token_bytes()`)

### 3. Secure Key Derivation (PBKDF2)

Encryption keys are derived using PBKDF2-HMAC-SHA256 with 100,000 iterations:

```python
# Key derivation happens automatically during encryption
encryption_key = APIKey._derive_encryption_key(user_salt)
```

**Security Properties:**
- OWASP recommended minimum of 100,000 iterations
- Uses SHA-256 as the underlying hash function
- Master password is Django's SECRET_KEY
- Each user gets a unique derived key

### 4. Optional Hashing for Verification-Only Keys

For keys that only need verification (not retrieval), use secure hashing:

```python
# Hash a key for verification-only storage
api_key.hash_key("user-api-key-value")

# Verify a key against the hash
is_valid = api_key.verify_key("provided-key-value")
```

**Security Properties:**
- Uses SHA-256 with user-specific salt
- Constant-time comparison using `secrets.compare_digest()`
- Keys cannot be recovered from hash

### 5. Secure Random Key Generation

API keys are generated using cryptographically secure random number generation:

```python
# Generate a new API key
key_value = APIKey.generate_api_key()  # 32-byte base64 encoded
```

**Security Properties:**
- Uses `secrets.token_bytes()` for cryptographic randomness
- 32-byte keys provide 256 bits of entropy
- Base64 encoded for safe transmission

## Usage Patterns

### Creating API Keys

Use the `CreateAPIKeyCommand` to create new API keys:

```python
from core.commands import CreateAPIKeyCommand

# Create encrypted key (for retrieval)
command = CreateAPIKeyCommand(
    user=user,
    name="my-service-key",
    scope="read_write",
    store_encrypted=True,  # Default
    expires_at=timezone.now() + timedelta(days=90),
    ip_address="192.168.1.1"
)
result = command.execute()

# Create hashed key (verification only)
command = CreateAPIKeyCommand(
    user=user,
    name="webhook-key",
    scope="write",
    store_encrypted=False,  # Store as hash only
)
result = command.execute()
```

### Verifying API Keys

Use the `VerifyAPIKeyCommand` for authentication:

```python
from core.commands import VerifyAPIKeyCommand

command = VerifyAPIKeyCommand(
    key_value="provided-api-key",
    ip_address="203.0.113.1"
)
result = command.execute()

if result['valid']:
    user = result['user']
    api_key_info = result['api_key']
    # Proceed with authenticated request
else:
    # Handle authentication failure
    pass
```

### Key Rotation

Rotate API keys periodically for security:

```python
from core.commands import RotateAPIKeyCommand

command = RotateAPIKeyCommand(
    user=user,
    api_key_uuid=str(api_key.uuid),
    ip_address="192.168.1.1"
)
result = command.execute()
new_key = result['new_key_value']
```

### Listing User Keys

List a user's API keys (without sensitive data):

```python
from core.commands import ListAPIKeysCommand

command = ListAPIKeysCommand(user=user, active_only=True)
result = command.execute()
api_keys = result['api_keys']
```

## Audit Logging

All API key operations are comprehensively logged:

### Logged Operations
- `created` - Key creation
- `used` - Successful key usage
- `rotated` - Key rotation
- `deactivated` - Key deactivation
- `deleted` - Key deletion
- `failed_auth` - Failed authentication attempts
- `expired` - Automatic expiration

### Audit Data Collected
- User information
- API key details
- IP address
- User agent string
- Operation timestamp
- Success/failure status
- Additional operation details

### Accessing Audit Logs

```python
from core.repositories import APIKeyAuditRepository

# Get user's audit logs
logs = APIKeyAuditRepository.get_user_audit_logs(user, limit=100)

# Get failed authentication attempts
failed_attempts = APIKeyAuditRepository.get_failed_auth_attempts(
    user, hours=24
)

# Cleanup old logs
deleted_count = APIKeyAuditRepository.cleanup_old_logs(days=90)
```

## Rate Limiting Support

The audit system provides data for implementing rate limiting:

```python
# Check failed authentication attempts from an IP
recent_failures = APIKeyAudit.objects.filter(
    action='failed_auth',
    ip_address='203.0.113.1',
    created_at__gte=timezone.now() - timedelta(hours=1)
).count()

if recent_failures > 10:
    # Implement rate limiting logic
    pass
```

## Management Commands

### Cleanup Expired Keys

```bash
python manage.py cleanup_expired_api_keys --days=90
```

This command:
- Deactivates expired API keys
- Removes old audit logs
- Logs all cleanup actions

### Create API Key for User

```bash
python manage.py create_api_key user@example.com "My API Key" \
    --scope=read_write \
    --expires-days=90 \
    --hash-only
```

## Security Best Practices

### For Developers

1. **Never log sensitive key values**
   ```python
   # DON'T
   logger.info(f"API key: {api_key_value}")
   
   # DO
   logger.info(f"API key created: {api_key.name} for {user.email}")
   ```

2. **Always use commands for business logic**
   ```python
   # DON'T
   api_key = APIKey.objects.create(...)
   api_key.encrypt_key(key_value)
   
   # DO
   command = CreateAPIKeyCommand(...)
   result = command.execute()
   ```

3. **Include IP tracking when possible**
   ```python
   command = VerifyAPIKeyCommand(
       key_value=key,
       ip_address=request.META.get('REMOTE_ADDR'),
       user_agent=request.META.get('HTTP_USER_AGENT')
   )
   ```

### For Administrators

1. **Regular key rotation**
   - Implement automated key rotation policies
   - Monitor key usage patterns
   - Deactivate unused keys

2. **Monitor audit logs**
   - Set up alerts for unusual patterns
   - Regular review of failed authentication attempts
   - Monitor for potential brute force attacks

3. **Backup and recovery**
   - Encrypted keys can be recovered if SECRET_KEY is preserved
   - Hashed keys cannot be recovered (by design)
   - Regular database backups include all key data

## Environment Configuration

### Required Settings

```python
# settings.py
SECRET_KEY = 'your-secret-key'  # Used for key derivation
```

### Optional Settings

```python
# Custom audit log retention
API_KEY_AUDIT_RETENTION_DAYS = 90

# Enable additional security logging
API_KEY_SECURITY_LOGGING = True
```

## Migration Guide

### For Existing Systems

If you have existing API keys, create a migration:

```python
# Example migration for existing keys
from django.db import migrations
from core.commands import CreateAPIKeyCommand

def migrate_existing_keys(apps, schema_editor):
    # Convert existing plain-text keys to encrypted storage
    pass  # Implement based on your existing system

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_add_api_key_models'),
    ]
    
    operations = [
        migrations.RunPython(migrate_existing_keys),
    ]
```

## Performance Considerations

### Encryption/Decryption Overhead
- Fernet encryption is fast for individual operations
- PBKDF2 key derivation adds ~1ms per operation
- Consider caching derived keys for high-throughput scenarios

### Database Indexing
The system includes optimized indexes:
- User + active status
- Expiration date
- Last used timestamp
- Audit log queries

### Audit Log Management
- Implement regular cleanup of old audit logs
- Consider archiving important audit data
- Monitor audit table size growth

## Troubleshooting

### Common Issues

1. **Decryption failures**
   - Check SECRET_KEY hasn't changed
   - Verify salt integrity
   - Check for database corruption

2. **Performance issues**
   - Monitor PBKDF2 iteration count
   - Check database indexes
   - Consider connection pooling

3. **Audit log growth**
   - Implement regular cleanup
   - Archive old logs if needed
   - Monitor disk space

### Debug Commands

```python
# Test encryption/decryption
api_key = APIKey.objects.get(...)
original_key = "test-key"
api_key.encrypt_key(original_key)
decrypted = api_key.decrypt_key()
assert original_key == decrypted

# Verify audit logging
command = CreateAPIKeyCommand(...)
result = command.execute()
audit_logs = APIKeyAudit.objects.filter(api_key__uuid=result['api_key']['uuid'])
```

## Security Considerations

### Threat Model

This implementation protects against:
- Database compromise (encrypted keys)
- Rainbow table attacks (user-specific salts)
- Timing attacks (constant-time comparison)
- Brute force attacks (audit logging for rate limiting)
- Privilege escalation (user isolation)

### Limitations

- Requires SECRET_KEY for key recovery
- PBKDF2 iterations add computational overhead
- Audit logs grow over time
- Not designed for extremely high-throughput scenarios

### Future Enhancements

Consider implementing:
- Hardware Security Module (HSM) integration
- Key escrow for enterprise environments
- Advanced rate limiting algorithms
- Automated key rotation schedules
- Integration with external key management systems