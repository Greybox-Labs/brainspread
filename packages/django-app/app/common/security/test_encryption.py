"""Tests for API key encryption utilities."""
import pytest
from django.test import TestCase

from .encryption import APIKeyEncryption


class TestAPIKeyEncryption(TestCase):
    """Test cases for API key encryption and hashing."""

    def setUp(self):
        """Set up test data."""
        self.test_api_key = "sk-test12345abcdef67890"
        self.user_id = 123

    def test_encrypt_decrypt_api_key(self):
        """Test that encryption and decryption work correctly."""
        # Encrypt the API key
        encrypted_data, salt = APIKeyEncryption.encrypt_api_key(
            self.test_api_key, self.user_id
        )
        
        # Verify we got encrypted data and salt
        self.assertTrue(encrypted_data)
        self.assertTrue(salt)
        self.assertNotEqual(encrypted_data, self.test_api_key)
        
        # Decrypt the API key
        decrypted_key = APIKeyEncryption.decrypt_api_key(
            encrypted_data, salt, self.user_id
        )
        
        # Verify decryption worked
        self.assertEqual(decrypted_key, self.test_api_key)

    def test_encrypt_decrypt_empty_key(self):
        """Test handling of empty API keys."""
        # Encrypt empty key
        encrypted_data, salt = APIKeyEncryption.encrypt_api_key("", self.user_id)
        self.assertEqual(encrypted_data, "")
        self.assertEqual(salt, "")
        
        # Decrypt empty key
        decrypted_key = APIKeyEncryption.decrypt_api_key("", "", self.user_id)
        self.assertIsNone(decrypted_key)

    def test_decrypt_with_wrong_user_id(self):
        """Test that decryption fails with wrong user ID."""
        # Encrypt with one user ID
        encrypted_data, salt = APIKeyEncryption.encrypt_api_key(
            self.test_api_key, self.user_id
        )
        
        # Try to decrypt with different user ID
        decrypted_key = APIKeyEncryption.decrypt_api_key(
            encrypted_data, salt, self.user_id + 1
        )
        
        # Should fail to decrypt
        self.assertIsNone(decrypted_key)

    def test_decrypt_with_invalid_data(self):
        """Test handling of invalid encrypted data."""
        # Try to decrypt invalid data
        decrypted_key = APIKeyEncryption.decrypt_api_key(
            "invalid_data", "invalid_salt", self.user_id
        )
        
        self.assertIsNone(decrypted_key)

    def test_unique_encryption_per_call(self):
        """Test that each encryption produces unique results due to salt."""
        # Encrypt the same key twice
        encrypted_data1, salt1 = APIKeyEncryption.encrypt_api_key(
            self.test_api_key, self.user_id
        )
        encrypted_data2, salt2 = APIKeyEncryption.encrypt_api_key(
            self.test_api_key, self.user_id
        )
        
        # Results should be different due to unique salts
        self.assertNotEqual(encrypted_data1, encrypted_data2)
        self.assertNotEqual(salt1, salt2)
        
        # But both should decrypt to the same key
        decrypted_key1 = APIKeyEncryption.decrypt_api_key(
            encrypted_data1, salt1, self.user_id
        )
        decrypted_key2 = APIKeyEncryption.decrypt_api_key(
            encrypted_data2, salt2, self.user_id
        )
        
        self.assertEqual(decrypted_key1, self.test_api_key)
        self.assertEqual(decrypted_key2, self.test_api_key)

    def test_hash_api_key_for_verification(self):
        """Test API key hashing for verification."""
        # Hash the API key
        api_key_hash, salt = APIKeyEncryption.hash_api_key_for_verification(
            self.test_api_key, self.user_id
        )
        
        # Verify we got hash and salt
        self.assertTrue(api_key_hash)
        self.assertTrue(salt)
        self.assertNotEqual(api_key_hash, self.test_api_key)

    def test_verify_api_key_hash(self):
        """Test API key verification against hash."""
        # Hash the API key
        api_key_hash, salt = APIKeyEncryption.hash_api_key_for_verification(
            self.test_api_key, self.user_id
        )
        
        # Verify correct key
        is_valid = APIKeyEncryption.verify_api_key_hash(
            self.test_api_key, api_key_hash, salt, self.user_id
        )
        self.assertTrue(is_valid)
        
        # Verify incorrect key
        is_valid = APIKeyEncryption.verify_api_key_hash(
            "wrong_key", api_key_hash, salt, self.user_id
        )
        self.assertFalse(is_valid)

    def test_verify_hash_with_wrong_user_id(self):
        """Test that hash verification fails with wrong user ID."""
        # Hash with one user ID
        api_key_hash, salt = APIKeyEncryption.hash_api_key_for_verification(
            self.test_api_key, self.user_id
        )
        
        # Try to verify with different user ID
        is_valid = APIKeyEncryption.verify_api_key_hash(
            self.test_api_key, api_key_hash, salt, self.user_id + 1
        )
        
        self.assertFalse(is_valid)

    def test_verify_hash_with_invalid_data(self):
        """Test handling of invalid hash data."""
        # Try to verify with invalid data
        is_valid = APIKeyEncryption.verify_api_key_hash(
            self.test_api_key, "invalid_hash", "invalid_salt", self.user_id
        )
        
        self.assertFalse(is_valid)

    def test_hash_empty_key(self):
        """Test hashing of empty API key."""
        api_key_hash, salt = APIKeyEncryption.hash_api_key_for_verification(
            "", self.user_id
        )
        
        self.assertEqual(api_key_hash, "")
        self.assertEqual(salt, "")

    def test_verify_empty_hash(self):
        """Test verification with empty hash."""
        is_valid = APIKeyEncryption.verify_api_key_hash(
            self.test_api_key, "", "", self.user_id
        )
        
        self.assertFalse(is_valid)

    def test_unique_hashes_per_call(self):
        """Test that each hash produces unique results due to salt."""
        # Hash the same key twice
        hash1, salt1 = APIKeyEncryption.hash_api_key_for_verification(
            self.test_api_key, self.user_id
        )
        hash2, salt2 = APIKeyEncryption.hash_api_key_for_verification(
            self.test_api_key, self.user_id
        )
        
        # Results should be different due to unique salts
        self.assertNotEqual(hash1, hash2)
        self.assertNotEqual(salt1, salt2)
        
        # But both should verify the same key
        is_valid1 = APIKeyEncryption.verify_api_key_hash(
            self.test_api_key, hash1, salt1, self.user_id
        )
        is_valid2 = APIKeyEncryption.verify_api_key_hash(
            self.test_api_key, hash2, salt2, self.user_id
        )
        
        self.assertTrue(is_valid1)
        self.assertTrue(is_valid2)