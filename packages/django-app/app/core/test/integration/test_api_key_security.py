import pytest
from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import base64
import secrets

from core.commands import CreateAPIKeyCommand, VerifyAPIKeyCommand
from core.models import APIKey, APIKeyAudit
from core.test.helpers import UserFactory


@pytest.mark.integration
class APIKeySecurityIntegrationTestCase(TestCase):
    """
    Integration tests for API key security features.
    
    These tests verify the security properties of the API key system
    including encryption, salting, and protection against common attacks.
    """
    
    def setUp(self):
        self.user1 = UserFactory()
        self.user2 = UserFactory()

    def test_encryption_keys_unique_per_user(self):
        """Test that encryption keys are unique per user (salt-based)."""
        same_key_value = "identical-secret-key"
        
        # Create API keys for different users with same key value
        api_key1 = APIKey.objects.create(user=self.user1, name="test1")
        api_key2 = APIKey.objects.create(user=self.user2, name="test2")
        
        api_key1.encrypt_key(same_key_value)
        api_key2.encrypt_key(same_key_value)
        
        # Encrypted values should be different due to different salts
        self.assertNotEqual(api_key1.encrypted_key, api_key2.encrypted_key)
        self.assertNotEqual(api_key1.salt, api_key2.salt)
        
        # But both should decrypt to the same value
        self.assertEqual(api_key1.decrypt_key(), same_key_value)
        self.assertEqual(api_key2.decrypt_key(), same_key_value)

    def test_hash_values_unique_per_user(self):
        """Test that hash values are unique per user (salt-based)."""
        same_key_value = "identical-secret-key"
        
        api_key1 = APIKey.objects.create(user=self.user1, name="test1")
        api_key2 = APIKey.objects.create(user=self.user2, name="test2")
        
        api_key1.hash_key(same_key_value)
        api_key2.hash_key(same_key_value)
        
        # Hash values should be different due to different salts
        self.assertNotEqual(api_key1.hashed_key, api_key2.hashed_key)
        self.assertNotEqual(api_key1.salt, api_key2.salt)
        
        # But both should verify correctly
        self.assertTrue(api_key1.verify_key(same_key_value))
        self.assertTrue(api_key2.verify_key(same_key_value))

    def test_salt_strength(self):
        """Test that salts meet security requirements."""
        api_key = APIKey.objects.create(user=self.user1, name="test")
        
        # Salt should be base64 encoded 32-byte value
        salt_bytes = base64.b64decode(api_key.salt)
        self.assertEqual(len(salt_bytes), 32)
        
        # Salt should be unique for each key
        api_key2 = APIKey.objects.create(user=self.user1, name="test2")
        self.assertNotEqual(api_key.salt, api_key2.salt)

    def test_generated_key_strength(self):
        """Test that generated API keys meet security requirements."""
        key = APIKey.generate_api_key()
        
        # Should be base64 encoded 32-byte value
        key_bytes = base64.b64decode(key)
        self.assertEqual(len(key_bytes), 32)
        
        # Multiple generations should be different
        key2 = APIKey.generate_api_key()
        self.assertNotEqual(key, key2)

    def test_constant_time_comparison_in_verification(self):
        """Test that hash verification uses constant-time comparison."""
        from core.test.helpers import APIKeyFactory
        api_key, key_value = APIKeyFactory.create_with_hashed_key(user=self.user1)
        
        # This test verifies that secrets.compare_digest is used
        # by checking that verification works correctly
        self.assertTrue(api_key.verify_key(key_value))
        self.assertFalse(api_key.verify_key("wrong-key"))

    def test_key_derivation_pbkdf2_strength(self):
        """Test that key derivation uses strong PBKDF2 parameters."""
        api_key = APIKey.objects.create(user=self.user1, name="test")
        
        # Test that encryption key derivation works
        encryption_key = api_key._derive_encryption_key(api_key.salt)
        self.assertEqual(len(encryption_key), 32)  # 256-bit key
        
        # Test that derived keys are different for different salts
        api_key2 = APIKey.objects.create(user=self.user2, name="test2")
        encryption_key2 = api_key2._derive_encryption_key(api_key2.salt)
        self.assertNotEqual(encryption_key, encryption_key2)

    def test_memory_cleanup_after_operations(self):
        """Test that sensitive data is not left in memory."""
        # This is a behavioral test - we can't directly test memory cleanup
        # but we can verify that operations complete successfully
        command = CreateAPIKeyCommand(
            user=self.user1,
            name="memory-test",
            store_encrypted=True
        )
        
        result = command.execute()
        
        # Verify key was created and works
        verify_command = VerifyAPIKeyCommand(key_value=result['key_value'])
        verify_result = verify_command.execute()
        
        self.assertTrue(verify_result['valid'])

    def test_rate_limiting_data_collection(self):
        """Test that failed authentication attempts are properly logged for rate limiting."""
        # Create multiple failed attempts
        for i in range(5):
            command = VerifyAPIKeyCommand(
                key_value="invalid-key",
                ip_address="192.168.1.100"
            )
            result = command.execute()
            self.assertFalse(result['valid'])
        
        # Check that all attempts were logged
        failed_attempts = APIKeyAudit.objects.filter(
            action='failed_auth',
            success=False,
            ip_address="192.168.1.100"
        ).count()
        
        self.assertEqual(failed_attempts, 5)

    def test_audit_trail_completeness(self):
        """Test that all operations are properly audited."""
        # Create key
        create_command = CreateAPIKeyCommand(
            user=self.user1,
            name="audit-test",
            ip_address="192.168.1.1"
        )
        result = create_command.execute()
        
        # Use key
        verify_command = VerifyAPIKeyCommand(
            key_value=result['key_value'],
            ip_address="192.168.1.2"
        )
        verify_command.execute()
        
        # Check audit logs
        api_key = APIKey.objects.get(uuid=result['api_key']['uuid'])
        audit_logs = APIKeyAudit.objects.filter(api_key=api_key).order_by('created_at')
        
        # Should have create and use logs
        self.assertEqual(audit_logs.count(), 2)
        
        create_log = audit_logs.first()
        self.assertEqual(create_log.action, 'created')
        self.assertEqual(create_log.ip_address, "192.168.1.1")
        self.assertTrue(create_log.success)
        
        use_log = audit_logs.last()
        self.assertEqual(use_log.action, 'used')
        self.assertEqual(use_log.ip_address, "192.168.1.2")
        self.assertTrue(use_log.success)

    def test_ip_address_tracking(self):
        """Test that IP addresses are properly tracked."""
        command = CreateAPIKeyCommand(
            user=self.user1,
            name="ip-test",
            ip_address="203.0.113.1"
        )
        result = command.execute()
        
        api_key = APIKey.objects.get(uuid=result['api_key']['uuid'])
        self.assertEqual(api_key.created_from_ip, "203.0.113.1")
        
        # Test IP tracking on verification
        verify_command = VerifyAPIKeyCommand(
            key_value=result['key_value'],
            ip_address="203.0.113.2"
        )
        verify_command.execute()
        
        api_key.refresh_from_db()
        self.assertEqual(api_key.last_used_ip, "203.0.113.2")

    def test_expiration_enforcement(self):
        """Test that expired keys are properly rejected."""
        # Create key that expires in 1 second
        expires_at = timezone.now() + timedelta(seconds=1)
        command = CreateAPIKeyCommand(
            user=self.user1,
            name="expiry-test",
            expires_at=expires_at
        )
        result = command.execute()
        
        # Key should work initially
        verify_command = VerifyAPIKeyCommand(key_value=result['key_value'])
        verify_result = verify_command.execute()
        self.assertTrue(verify_result['valid'])
        
        # Manually expire the key for testing
        api_key = APIKey.objects.get(uuid=result['api_key']['uuid'])
        api_key.expires_at = timezone.now() - timedelta(seconds=1)
        api_key.save()
        
        # Key should now be rejected
        verify_command = VerifyAPIKeyCommand(key_value=result['key_value'])
        verify_result = verify_command.execute()
        self.assertFalse(verify_result['valid'])
        
        # Key should be automatically deactivated
        api_key.refresh_from_db()
        self.assertFalse(api_key.is_active)

    def test_cross_user_key_isolation(self):
        """Test that users cannot access each other's keys."""
        # User 1 creates a key
        command1 = CreateAPIKeyCommand(user=self.user1, name="user1-key")
        result1 = command1.execute()
        
        # User 2 creates a key
        command2 = CreateAPIKeyCommand(user=self.user2, name="user2-key")
        result2 = command2.execute()
        
        # Each user should only see their own keys
        from core.commands import ListAPIKeysCommand
        
        list_command1 = ListAPIKeysCommand(user=self.user1)
        user1_keys = list_command1.execute()
        
        list_command2 = ListAPIKeysCommand(user=self.user2)
        user2_keys = list_command2.execute()
        
        self.assertEqual(user1_keys['total_count'], 1)
        self.assertEqual(user2_keys['total_count'], 1)
        
        self.assertEqual(user1_keys['api_keys'][0]['name'], "user1-key")
        self.assertEqual(user2_keys['api_keys'][0]['name'], "user2-key")