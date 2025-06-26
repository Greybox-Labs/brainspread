"""Tests for secure API key storage in UserProviderConfig model."""
import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AIProvider, UserProviderConfig

User = get_user_model()


class TestSecureAPIKeyStorage(TestCase):
    """Test cases for secure API key storage functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.provider = AIProvider.objects.create(
            name='OpenAI',
            base_url='https://api.openai.com'
        )
        self.test_api_key = "sk-test12345abcdef67890"

    def test_set_and_get_encrypted_api_key(self):
        """Test setting and getting an encrypted API key."""
        config = UserProviderConfig.objects.create(
            user=self.user,
            provider=self.provider
        )
        
        # Set the API key (encrypted mode)
        success = config.set_api_key(self.test_api_key, hash_only=False)
        self.assertTrue(success)
        
        # Verify encrypted fields are populated
        self.assertTrue(config.encrypted_api_key)
        self.assertTrue(config.api_key_salt)
        self.assertEqual(config.api_key_hash, "")
        self.assertEqual(config.api_key_hash_salt, "")
        self.assertEqual(config.api_key, "")  # Legacy field should be cleared
        
        # Verify we can retrieve the key
        retrieved_key = config.get_api_key()
        self.assertEqual(retrieved_key, self.test_api_key)
        
        # Verify has_api_key returns True
        self.assertTrue(config.has_api_key())

    def test_set_and_verify_hashed_api_key(self):
        """Test setting and verifying a hash-only API key."""
        config = UserProviderConfig.objects.create(
            user=self.user,
            provider=self.provider
        )
        
        # Set the API key (hash-only mode)
        success = config.set_api_key(self.test_api_key, hash_only=True)
        self.assertTrue(success)
        
        # Verify hash fields are populated
        self.assertTrue(config.api_key_hash)
        self.assertTrue(config.api_key_hash_salt)
        self.assertEqual(config.encrypted_api_key, "")
        self.assertEqual(config.api_key_salt, "")
        self.assertEqual(config.api_key, "")  # Legacy field should be cleared
        
        # Verify we cannot retrieve the key (hash-only)
        retrieved_key = config.get_api_key()
        self.assertIsNone(retrieved_key)
        
        # Verify we can verify the key
        is_valid = config.verify_api_key(self.test_api_key)
        self.assertTrue(is_valid)
        
        # Verify wrong key fails verification
        is_valid = config.verify_api_key("wrong_key")
        self.assertFalse(is_valid)
        
        # Verify has_api_key returns True
        self.assertTrue(config.has_api_key())

    def test_legacy_api_key_compatibility(self):
        """Test that legacy plain-text API keys still work."""
        config = UserProviderConfig.objects.create(
            user=self.user,
            provider=self.provider,
            api_key=self.test_api_key  # Set legacy field directly
        )
        
        # Should be able to get the key
        retrieved_key = config.get_api_key()
        self.assertEqual(retrieved_key, self.test_api_key)
        
        # Should report having an API key
        self.assertTrue(config.has_api_key())

    def test_clear_api_key(self):
        """Test clearing API key data."""
        config = UserProviderConfig.objects.create(
            user=self.user,
            provider=self.provider
        )
        
        # Set encrypted key first
        config.set_api_key(self.test_api_key, hash_only=False)
        self.assertTrue(config.has_api_key())
        
        # Clear the key
        config.clear_api_key()
        
        # Verify all fields are cleared
        self.assertEqual(config.api_key, "")
        self.assertEqual(config.encrypted_api_key, "")
        self.assertEqual(config.api_key_salt, "")
        self.assertEqual(config.api_key_hash, "")
        self.assertEqual(config.api_key_hash_salt, "")
        
        # Verify has_api_key returns False
        self.assertFalse(config.has_api_key())
        
        # Verify get_api_key returns None
        self.assertIsNone(config.get_api_key())

    def test_set_empty_api_key(self):
        """Test setting an empty API key."""
        config = UserProviderConfig.objects.create(
            user=self.user,
            provider=self.provider
        )
        
        # Set empty key
        success = config.set_api_key("", hash_only=False)
        self.assertTrue(success)
        
        # Should clear all fields
        self.assertFalse(config.has_api_key())
        self.assertIsNone(config.get_api_key())

    def test_verify_with_encrypted_key_fallback(self):
        """Test that verify_api_key falls back to decryption when no hash exists."""
        config = UserProviderConfig.objects.create(
            user=self.user,
            provider=self.provider
        )
        
        # Set encrypted key (not hash-only)
        config.set_api_key(self.test_api_key, hash_only=False)
        
        # Verify should work by decrypting
        is_valid = config.verify_api_key(self.test_api_key)
        self.assertTrue(is_valid)
        
        # Wrong key should fail
        is_valid = config.verify_api_key("wrong_key")
        self.assertFalse(is_valid)

    def test_cross_user_isolation(self):
        """Test that API keys are isolated between users."""
        # Create second user
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create configs for both users
        config1 = UserProviderConfig.objects.create(
            user=self.user,
            provider=self.provider
        )
        config2 = UserProviderConfig.objects.create(
            user=user2,
            provider=self.provider
        )
        
        # Set keys for both users
        config1.set_api_key(self.test_api_key, hash_only=False)
        config2.set_api_key("different_key", hash_only=False)
        
        # Each user should get their own key
        self.assertEqual(config1.get_api_key(), self.test_api_key)
        self.assertEqual(config2.get_api_key(), "different_key")
        
        # Keys should be encrypted differently (different salts)
        self.assertNotEqual(config1.encrypted_api_key, config2.encrypted_api_key)
        self.assertNotEqual(config1.api_key_salt, config2.api_key_salt)

    def test_encryption_uniqueness(self):
        """Test that each encryption produces unique results."""
        config = UserProviderConfig.objects.create(
            user=self.user,
            provider=self.provider
        )
        
        # Encrypt the same key twice
        config.set_api_key(self.test_api_key, hash_only=False)
        first_encrypted = config.encrypted_api_key
        first_salt = config.api_key_salt
        
        config.set_api_key(self.test_api_key, hash_only=False)
        second_encrypted = config.encrypted_api_key
        second_salt = config.api_key_salt
        
        # Should be different due to new salt
        self.assertNotEqual(first_encrypted, second_encrypted)
        self.assertNotEqual(first_salt, second_salt)
        
        # But should still decrypt to the same key
        self.assertEqual(config.get_api_key(), self.test_api_key)