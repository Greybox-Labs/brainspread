"""
Encryption utilities for sensitive data storage.

This module provides field-level encryption for sensitive data like API keys
with user-specific salting and secure key derivation.
"""
import base64
import hashlib
import secrets
from typing import Optional, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings


class APIKeyEncryption:
    """Handles encryption and decryption of API keys with user-specific salting."""
    
    # PBKDF2 iterations - using OWASP recommended minimum
    PBKDF2_ITERATIONS = 100_000
    
    # Salt length in bytes
    SALT_LENGTH = 32
    
    @classmethod
    def _get_encryption_key(cls, user_id: int, salt: bytes) -> bytes:
        """
        Derive encryption key using PBKDF2 with user-specific salt.
        
        Args:
            user_id: The user's ID for key derivation
            salt: The salt for key derivation
            
        Returns:
            32-byte encryption key suitable for Fernet
        """
        # Use Django secret key + user ID as password material
        password = f"{settings.SECRET_KEY}:{user_id}".encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=cls.PBKDF2_ITERATIONS,
        )
        
        key = kdf.derive(password)
        return base64.urlsafe_b64encode(key)

    @classmethod
    def _generate_salt(cls) -> bytes:
        """Generate a cryptographically secure random salt."""
        return secrets.token_bytes(cls.SALT_LENGTH)

    @classmethod
    def encrypt_api_key(cls, api_key: str, user_id: int) -> Tuple[str, str]:
        """
        Encrypt an API key with user-specific encryption.
        
        Args:
            api_key: The plaintext API key to encrypt
            user_id: The user's ID for key derivation
            
        Returns:
            Tuple of (encrypted_data, salt) both base64 encoded
        """
        if not api_key:
            return "", ""
            
        # Generate new salt for this encryption
        salt = cls._generate_salt()
        
        # Derive encryption key
        encryption_key = cls._get_encryption_key(user_id, salt)
        
        # Encrypt the API key
        cipher = Fernet(encryption_key)
        encrypted_data = cipher.encrypt(api_key.encode('utf-8'))
        
        # Return both as base64 encoded strings
        return (
            base64.urlsafe_b64encode(encrypted_data).decode('utf-8'),
            base64.urlsafe_b64encode(salt).decode('utf-8')
        )

    @classmethod
    def decrypt_api_key(cls, encrypted_data: str, salt: str, user_id: int) -> Optional[str]:
        """
        Decrypt an encrypted API key.
        
        Args:
            encrypted_data: The base64 encoded encrypted data
            salt: The base64 encoded salt
            user_id: The user's ID for key derivation
            
        Returns:
            Decrypted API key or None if decryption fails
        """
        if not encrypted_data or not salt:
            return None
            
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            salt_bytes = base64.urlsafe_b64decode(salt.encode('utf-8'))
            
            # Derive encryption key
            encryption_key = cls._get_encryption_key(user_id, salt_bytes)
            
            # Decrypt the data
            cipher = Fernet(encryption_key)
            decrypted_data = cipher.decrypt(encrypted_bytes)
            
            return decrypted_data.decode('utf-8')
            
        except Exception:
            # Log the error but don't expose details for security
            return None

    @classmethod
    def hash_api_key_for_verification(cls, api_key: str, user_id: int) -> Tuple[str, str]:
        """
        Create a hash of an API key for verification purposes only.
        Use this when you only need to verify a key, not retrieve it.
        
        Args:
            api_key: The plaintext API key to hash
            user_id: The user's ID for salt generation
            
        Returns:
            Tuple of (hash, salt) both base64 encoded
        """
        if not api_key:
            return "", ""
            
        # Generate salt
        salt = cls._generate_salt()
        
        # Create hash with user-specific salt
        hash_input = f"{api_key}:{user_id}".encode('utf-8')
        hash_obj = hashlib.sha256()
        hash_obj.update(salt)
        hash_obj.update(hash_input)
        
        api_key_hash = hash_obj.digest()
        
        return (
            base64.urlsafe_b64encode(api_key_hash).decode('utf-8'),
            base64.urlsafe_b64encode(salt).decode('utf-8')
        )

    @classmethod
    def verify_api_key_hash(cls, api_key: str, stored_hash: str, salt: str, user_id: int) -> bool:
        """
        Verify an API key against its stored hash.
        
        Args:
            api_key: The plaintext API key to verify
            stored_hash: The base64 encoded stored hash
            salt: The base64 encoded salt
            user_id: The user's ID
            
        Returns:
            True if the key matches the hash
        """
        if not all([api_key, stored_hash, salt]):
            return False
            
        try:
            # Decode stored hash and salt
            stored_hash_bytes = base64.urlsafe_b64decode(stored_hash.encode('utf-8'))
            salt_bytes = base64.urlsafe_b64decode(salt.encode('utf-8'))
            
            # Generate hash of provided key
            hash_input = f"{api_key}:{user_id}".encode('utf-8')
            hash_obj = hashlib.sha256()
            hash_obj.update(salt_bytes)
            hash_obj.update(hash_input)
            
            computed_hash = hash_obj.digest()
            
            # Use constant-time comparison to prevent timing attacks
            return secrets.compare_digest(stored_hash_bytes, computed_hash)
            
        except Exception:
            return False