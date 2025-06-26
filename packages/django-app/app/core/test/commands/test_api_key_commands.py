from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from core.commands import (
    CreateAPIKeyCommand,
    VerifyAPIKeyCommand,
    RotateAPIKeyCommand,
    DeactivateAPIKeyCommand,
    ListAPIKeysCommand,
)
from core.models import APIKey, APIKeyAudit
from core.test.helpers import UserFactory, APIKeyFactory


class CreateAPIKeyCommandTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_create_encrypted_api_key(self):
        """Test creating an encrypted API key."""
        command = CreateAPIKeyCommand(
            user=self.user,
            name="test-key",
            scope="read_write",
            store_encrypted=True,
            ip_address="192.168.1.1",
        )
        
        result = command.execute()
        
        # Check result structure
        self.assertIn('api_key', result)
        self.assertIn('key_value', result)
        self.assertEqual(result['storage_type'], 'encrypted')
        
        # Check API key was saved
        api_key = APIKey.objects.get(uuid=result['api_key']['uuid'])
        self.assertEqual(api_key.user, self.user)
        self.assertEqual(api_key.name, "test-key")
        self.assertEqual(api_key.scope, "read_write")
        self.assertTrue(api_key.encrypted_key)
        self.assertIsNone(api_key.hashed_key)
        
        # Check decryption works
        decrypted = api_key.decrypt_key()
        self.assertEqual(decrypted, result['key_value'])
        
        # Check audit log was created
        audit = APIKeyAudit.objects.filter(api_key=api_key, action='created').first()
        self.assertIsNotNone(audit)
        self.assertTrue(audit.success)

    def test_create_hashed_api_key(self):
        """Test creating a hashed API key."""
        command = CreateAPIKeyCommand(
            user=self.user,
            name="test-key-hash",
            scope="read",
            store_encrypted=False,
        )
        
        result = command.execute()
        
        # Check result structure
        self.assertEqual(result['storage_type'], 'hashed')
        
        # Check API key was saved
        api_key = APIKey.objects.get(uuid=result['api_key']['uuid'])
        self.assertTrue(api_key.hashed_key)
        self.assertIsNone(api_key.encrypted_key)
        
        # Check verification works
        self.assertTrue(api_key.verify_key(result['key_value']))

    def test_create_api_key_with_expiration(self):
        """Test creating an API key with expiration."""
        expires_at = timezone.now() + timedelta(days=30)
        
        command = CreateAPIKeyCommand(
            user=self.user,
            name="expiring-key",
            expires_at=expires_at,
        )
        
        result = command.execute()
        
        api_key = APIKey.objects.get(uuid=result['api_key']['uuid'])
        self.assertEqual(api_key.expires_at, expires_at)

    def test_create_duplicate_key_name_fails(self):
        """Test that creating a key with duplicate name fails."""
        # Create first key
        APIKeyFactory(user=self.user, name="duplicate-name")
        
        # Try to create another with same name
        command = CreateAPIKeyCommand(
            user=self.user,
            name="duplicate-name",
        )
        
        with self.assertRaises(ValueError) as context:
            command.execute()
        
        self.assertIn("already exists", str(context.exception))
        
        # Check that failure was logged
        audit = APIKeyAudit.objects.filter(
            user=self.user,
            action='created',
            success=False
        ).first()
        self.assertIsNotNone(audit)


class VerifyAPIKeyCommandTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_verify_encrypted_key_success(self):
        """Test successful verification of encrypted key."""
        api_key, key_value = APIKeyFactory.create_with_encrypted_key(user=self.user)
        
        command = VerifyAPIKeyCommand(
            key_value=key_value,
            ip_address="192.168.1.1",
        )
        
        result = command.execute()
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['user']['uuid'], str(self.user.uuid))
        self.assertEqual(result['api_key']['uuid'], str(api_key.uuid))
        
        # Check that usage was logged
        audit = APIKeyAudit.objects.filter(
            api_key=api_key,
            action='used'
        ).first()
        self.assertIsNotNone(audit)

    def test_verify_hashed_key_success(self):
        """Test successful verification of hashed key."""
        api_key, key_value = APIKeyFactory.create_with_hashed_key(user=self.user)
        
        command = VerifyAPIKeyCommand(key_value=key_value)
        result = command.execute()
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['user']['uuid'], str(self.user.uuid))

    def test_verify_invalid_key(self):
        """Test verification with invalid key."""
        APIKeyFactory.create_with_encrypted_key(user=self.user)
        
        command = VerifyAPIKeyCommand(key_value="invalid-key")
        result = command.execute()
        
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
        
        # Check that failure was logged
        audit = APIKeyAudit.objects.filter(
            action='failed_auth',
            success=False
        ).first()
        self.assertIsNotNone(audit)

    def test_verify_expired_key(self):
        """Test verification of expired key."""
        expired_key = APIKeyFactory.create_expired(user=self.user)
        key_value = APIKey.generate_api_key()
        expired_key.encrypt_key(key_value)
        expired_key.save()
        
        command = VerifyAPIKeyCommand(key_value=key_value)
        result = command.execute()
        
        self.assertFalse(result['valid'])
        
        # Check that key was deactivated
        expired_key.refresh_from_db()
        self.assertFalse(expired_key.is_active)
        
        # Check that expiration was logged
        audit = APIKeyAudit.objects.filter(
            api_key=expired_key,
            action='expired'
        ).first()
        self.assertIsNotNone(audit)

    def test_verify_inactive_key(self):
        """Test verification of inactive key."""
        api_key, key_value = APIKeyFactory.create_with_encrypted_key(
            user=self.user,
            is_active=False
        )
        
        command = VerifyAPIKeyCommand(key_value=key_value)
        result = command.execute()
        
        self.assertFalse(result['valid'])


class RotateAPIKeyCommandTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_rotate_encrypted_key(self):
        """Test rotating an encrypted API key."""
        api_key, old_key_value = APIKeyFactory.create_with_encrypted_key(user=self.user)
        
        command = RotateAPIKeyCommand(
            user=self.user,
            api_key_uuid=str(api_key.uuid),
        )
        
        result = command.execute()
        
        # Check result structure
        self.assertIn('new_key_value', result)
        self.assertEqual(result['storage_type'], 'encrypted')
        self.assertNotEqual(result['new_key_value'], old_key_value)
        
        # Check that old key no longer works
        api_key.refresh_from_db()
        self.assertNotEqual(api_key.decrypt_key(), old_key_value)
        self.assertEqual(api_key.decrypt_key(), result['new_key_value'])
        
        # Check that rotation was logged
        audit = APIKeyAudit.objects.filter(
            api_key=api_key,
            action='rotated'
        ).first()
        self.assertIsNotNone(audit)

    def test_rotate_hashed_key(self):
        """Test rotating a hashed API key."""
        api_key, old_key_value = APIKeyFactory.create_with_hashed_key(user=self.user)
        
        command = RotateAPIKeyCommand(
            user=self.user,
            api_key_uuid=str(api_key.uuid),
        )
        
        result = command.execute()
        
        # Check result structure
        self.assertEqual(result['storage_type'], 'hashed')
        
        # Check that old key no longer works
        api_key.refresh_from_db()
        self.assertFalse(api_key.verify_key(old_key_value))
        self.assertTrue(api_key.verify_key(result['new_key_value']))

    def test_rotate_nonexistent_key(self):
        """Test rotating a nonexistent API key."""
        command = RotateAPIKeyCommand(
            user=self.user,
            api_key_uuid="nonexistent-uuid",
        )
        
        with self.assertRaises(ValueError) as context:
            command.execute()
        
        self.assertIn("not found", str(context.exception))

    def test_rotate_other_users_key(self):
        """Test rotating another user's API key."""
        other_user = UserFactory()
        api_key, _ = APIKeyFactory.create_with_encrypted_key(user=other_user)
        
        command = RotateAPIKeyCommand(
            user=self.user,
            api_key_uuid=str(api_key.uuid),
        )
        
        with self.assertRaises(ValueError) as context:
            command.execute()
        
        self.assertIn("does not belong", str(context.exception))

    def test_rotate_inactive_key(self):
        """Test rotating an inactive API key."""
        api_key, _ = APIKeyFactory.create_with_encrypted_key(
            user=self.user,
            is_active=False
        )
        
        command = RotateAPIKeyCommand(
            user=self.user,
            api_key_uuid=str(api_key.uuid),
        )
        
        with self.assertRaises(ValueError) as context:
            command.execute()
        
        self.assertIn("inactive", str(context.exception))


class DeactivateAPIKeyCommandTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_deactivate_active_key(self):
        """Test deactivating an active API key."""
        api_key = APIKeyFactory(user=self.user, is_active=True)
        
        command = DeactivateAPIKeyCommand(
            user=self.user,
            api_key_uuid=str(api_key.uuid),
        )
        
        result = command.execute()
        
        # Check result
        self.assertFalse(result['api_key']['is_active'])
        
        # Check that key was deactivated in database
        api_key.refresh_from_db()
        self.assertFalse(api_key.is_active)
        
        # Check that deactivation was logged
        audit = APIKeyAudit.objects.filter(
            api_key=api_key,
            action='deactivated'
        ).first()
        self.assertIsNotNone(audit)

    def test_deactivate_already_inactive_key(self):
        """Test deactivating an already inactive API key."""
        api_key = APIKeyFactory(user=self.user, is_active=False)
        
        command = DeactivateAPIKeyCommand(
            user=self.user,
            api_key_uuid=str(api_key.uuid),
        )
        
        with self.assertRaises(ValueError) as context:
            command.execute()
        
        self.assertIn("already inactive", str(context.exception))


class ListAPIKeysCommandTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_list_active_keys_only(self):
        """Test listing only active API keys."""
        active_key = APIKeyFactory(user=self.user, is_active=True)
        inactive_key = APIKeyFactory(user=self.user, is_active=False)
        
        command = ListAPIKeysCommand(user=self.user, active_only=True)
        result = command.execute()
        
        self.assertEqual(result['total_count'], 1)
        self.assertTrue(result['active_only'])
        self.assertEqual(result['api_keys'][0]['uuid'], str(active_key.uuid))

    def test_list_all_keys(self):
        """Test listing all API keys."""
        active_key = APIKeyFactory(user=self.user, is_active=True)
        inactive_key = APIKeyFactory(user=self.user, is_active=False)
        
        command = ListAPIKeysCommand(user=self.user, active_only=False)
        result = command.execute()
        
        self.assertEqual(result['total_count'], 2)
        self.assertFalse(result['active_only'])

    def test_list_keys_shows_storage_type(self):
        """Test that listing shows storage type."""
        encrypted_key, _ = APIKeyFactory.create_with_encrypted_key(user=self.user)
        hashed_key, _ = APIKeyFactory.create_with_hashed_key(user=self.user)
        
        command = ListAPIKeysCommand(user=self.user)
        result = command.execute()
        
        storage_types = [key['storage_type'] for key in result['api_keys']]
        self.assertIn('encrypted', storage_types)
        self.assertIn('hashed', storage_types)

    def test_list_keys_excludes_sensitive_data(self):
        """Test that listing doesn't include sensitive key data."""
        api_key, _ = APIKeyFactory.create_with_encrypted_key(user=self.user)
        
        command = ListAPIKeysCommand(user=self.user)
        result = command.execute()
        
        key_data = result['api_keys'][0]
        
        # Should not include sensitive fields
        self.assertNotIn('encrypted_key', key_data)
        self.assertNotIn('hashed_key', key_data)
        self.assertNotIn('salt', key_data)
        
        # Should include safe fields
        self.assertIn('uuid', key_data)
        self.assertIn('name', key_data)
        self.assertIn('scope', key_data)
        self.assertIn('is_active', key_data)