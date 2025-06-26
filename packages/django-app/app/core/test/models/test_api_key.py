from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import base64
import secrets

from core.models import APIKey, APIKeyAudit
from core.test.helpers import UserFactory, APIKeyFactory


class APIKeyModelTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_api_key_creation_with_salt(self):
        """Test that API key is created with a salt."""
        api_key = APIKeyFactory(user=self.user)
        
        self.assertTrue(api_key.salt)
        self.assertEqual(len(base64.b64decode(api_key.salt)), 32)  # 32-byte salt

    def test_generate_api_key(self):
        """Test API key generation."""
        key = APIKey.generate_api_key()
        
        self.assertTrue(key)
        self.assertEqual(len(base64.b64decode(key)), 32)  # 32-byte key

    def test_encrypt_and_decrypt_key(self):
        """Test key encryption and decryption."""
        api_key = APIKeyFactory(user=self.user)
        original_key = "test-api-key-12345"
        
        # Encrypt the key
        api_key.encrypt_key(original_key)
        self.assertTrue(api_key.encrypted_key)
        self.assertIsNone(api_key.hashed_key)  # Should clear hashed key
        
        # Decrypt the key
        decrypted_key = api_key.decrypt_key()
        self.assertEqual(decrypted_key, original_key)

    def test_encrypt_empty_key_raises_error(self):
        """Test that encrypting empty key raises error."""
        api_key = APIKeyFactory(user=self.user)
        
        with self.assertRaises(ValueError):
            api_key.encrypt_key("")

    def test_hash_and_verify_key(self):
        """Test key hashing and verification."""
        api_key = APIKeyFactory(user=self.user)
        original_key = "test-api-key-12345"
        
        # Hash the key
        api_key.hash_key(original_key)
        self.assertTrue(api_key.hashed_key)
        self.assertIsNone(api_key.encrypted_key)  # Should clear encrypted key
        
        # Verify the key
        self.assertTrue(api_key.verify_key(original_key))
        self.assertFalse(api_key.verify_key("wrong-key"))

    def test_hash_empty_key_raises_error(self):
        """Test that hashing empty key raises error."""
        api_key = APIKeyFactory(user=self.user)
        
        with self.assertRaises(ValueError):
            api_key.hash_key("")

    def test_verify_key_with_no_hash(self):
        """Test verifying key when no hash is stored."""
        api_key = APIKeyFactory(user=self.user)
        
        self.assertFalse(api_key.verify_key("any-key"))

    def test_decrypt_key_with_no_encryption(self):
        """Test decrypting key when no encrypted key is stored."""
        api_key = APIKeyFactory(user=self.user)
        
        self.assertIsNone(api_key.decrypt_key())

    def test_user_specific_salt_different_keys(self):
        """Test that different users get different salts."""
        user1 = UserFactory()
        user2 = UserFactory()
        
        api_key1 = APIKeyFactory(user=user1)
        api_key2 = APIKeyFactory(user=user2)
        
        self.assertNotEqual(api_key1.salt, api_key2.salt)

    def test_encryption_key_derivation_user_specific(self):
        """Test that encryption keys are different for different users."""
        user1 = UserFactory()
        user2 = UserFactory()
        
        api_key1 = APIKeyFactory(user=user1)
        api_key2 = APIKeyFactory(user=user2)
        
        same_key_value = "identical-key-value"
        
        api_key1.encrypt_key(same_key_value)
        api_key2.encrypt_key(same_key_value)
        
        # Encrypted values should be different due to different salts
        self.assertNotEqual(api_key1.encrypted_key, api_key2.encrypted_key)
        
        # But both should decrypt to the same value
        self.assertEqual(api_key1.decrypt_key(), same_key_value)
        self.assertEqual(api_key2.decrypt_key(), same_key_value)

    def test_string_representation(self):
        """Test string representation of API key."""
        api_key = APIKeyFactory(user=self.user, name="test-key")
        
        expected = f"{self.user.email} - test-key"
        self.assertEqual(str(api_key), expected)

    def test_unique_together_constraint(self):
        """Test that user-name combination is unique."""
        # Create first API key
        APIKeyFactory(user=self.user, name="unique-name")
        
        # Try to create another with same user and name
        with self.assertRaises(Exception):  # This should fail due to unique_together
            APIKeyFactory(user=self.user, name="unique-name")

    def test_scope_choices(self):
        """Test that scope field accepts valid choices."""
        valid_scopes = ['read', 'write', 'read_write', 'admin']
        
        for scope in valid_scopes:
            api_key = APIKeyFactory(user=self.user, scope=scope)
            self.assertEqual(api_key.scope, scope)

    def test_expired_key_handling(self):
        """Test expired key detection."""
        # Create expired key
        expired_key = APIKeyFactory(
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        # Create active key
        active_key = APIKeyFactory(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Check expiration
        now = timezone.now()
        self.assertTrue(expired_key.expires_at < now)
        self.assertTrue(active_key.expires_at > now)


class APIKeyAuditModelTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.api_key = APIKeyFactory(user=self.user)

    def test_audit_log_creation(self):
        """Test creating an audit log entry."""
        audit = APIKeyAudit.log_operation(
            user=self.user,
            api_key=self.api_key,
            action='created',
            ip_address='192.168.1.1',
            user_agent='Test Agent',
            details={'test': 'data'}
        )
        
        self.assertEqual(audit.user, self.user)
        self.assertEqual(audit.api_key, self.api_key)
        self.assertEqual(audit.action, 'created')
        self.assertEqual(audit.ip_address, '192.168.1.1')
        self.assertEqual(audit.user_agent, 'Test Agent')
        self.assertEqual(audit.details, {'test': 'data'})
        self.assertTrue(audit.success)

    def test_audit_log_failure(self):
        """Test creating an audit log for a failed operation."""
        audit = APIKeyAudit.log_operation(
            user=self.user,
            api_key=None,
            action='failed_auth',
            success=False,
            error_message='Invalid key'
        )
        
        self.assertEqual(audit.user, self.user)
        self.assertIsNone(audit.api_key)
        self.assertEqual(audit.action, 'failed_auth')
        self.assertFalse(audit.success)
        self.assertEqual(audit.error_message, 'Invalid key')

    def test_audit_string_representation(self):
        """Test string representation of audit log."""
        audit = APIKeyAudit.log_operation(
            user=self.user,
            api_key=self.api_key,
            action='created'
        )
        
        expected = f"{self.user.email} - created - {self.api_key.name} - SUCCESS"
        self.assertEqual(str(audit), expected)

    def test_audit_string_representation_failure(self):
        """Test string representation of failed audit log."""
        audit = APIKeyAudit.log_operation(
            user=self.user,
            api_key=self.api_key,
            action='created',
            success=False
        )
        
        expected = f"{self.user.email} - created - {self.api_key.name} - FAILED"
        self.assertEqual(str(audit), expected)

    def test_audit_action_choices(self):
        """Test that audit action field accepts valid choices."""
        valid_actions = ['created', 'used', 'rotated', 'deactivated', 'deleted', 'failed_auth', 'expired']
        
        for action in valid_actions:
            audit = APIKeyAudit.log_operation(
                user=self.user,
                api_key=self.api_key,
                action=action
            )
            self.assertEqual(audit.action, action)