from typing import Optional
import secrets
import hashlib
import base64
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.soft_delete_timestamp_mixin import SoftDeleteTimestampMixin
from common.models.uuid_mixin import UUIDModelMixin


class APIKey(
    UUIDModelMixin,
    CRUDTimestampsMixin,
    SoftDeleteTimestampMixin,
):
    """
    Secure API key storage model with encryption, salting, and hashing.
    
    Security features:
    - Field-level encryption for retrievable keys
    - User-specific salting to prevent rainbow table attacks
    - Optional hashing for verification-only keys
    - Secure key derivation using PBKDF2
    """
    
    SCOPE_CHOICES = [
        ('read', _('Read Only')),
        ('write', _('Write Only')),
        ('read_write', _('Read and Write')),
        ('admin', _('Administrative')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='api_keys',
        help_text=_('User who owns this API key'),
    )
    
    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_('Human-readable name for this API key'),
    )
    
    # Encrypted storage for keys that need to be retrieved
    encrypted_key = models.TextField(
        _('encrypted key'),
        blank=True,
        null=True,
        help_text=_('Encrypted API key value for retrieval'),
    )
    
    # Hashed storage for keys that only need verification
    hashed_key = models.CharField(
        _('hashed key'),
        max_length=128,
        blank=True,
        null=True,
        help_text=_('Hashed API key value for verification only'),
    )
    
    # User-specific salt for additional security
    salt = models.CharField(
        _('salt'),
        max_length=44,  # Base64 encoded 32-byte salt
        help_text=_('User-specific salt for key derivation'),
    )
    
    scope = models.CharField(
        _('scope'),
        max_length=20,
        choices=SCOPE_CHOICES,
        default='read',
        help_text=_('API key permissions scope'),
    )
    
    last_used = models.DateTimeField(
        _('last used'),
        blank=True,
        null=True,
        help_text=_('Timestamp of last API key usage'),
    )
    
    expires_at = models.DateTimeField(
        _('expires at'),
        blank=True,
        null=True,
        help_text=_('Optional expiration date for the API key'),
    )
    
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether this API key is currently active'),
    )
    
    # Audit fields
    created_from_ip = models.GenericIPAddressField(
        _('created from IP'),
        blank=True,
        null=True,
        help_text=_('IP address where this key was created'),
    )
    
    last_used_ip = models.GenericIPAddressField(
        _('last used IP'),
        blank=True,  
        null=True,
        help_text=_('IP address where this key was last used'),
    )
    
    def save(self, *args, **kwargs):
        """Generate salt on creation if not provided."""
        if not self.salt:
            self.salt = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
        super().save(*args, **kwargs)
    
    @classmethod
    def _derive_encryption_key(cls, user_salt: str) -> bytes:
        """
        Derive encryption key using PBKDF2 with user-specific salt.
        
        Args:
            user_salt: Base64 encoded user-specific salt
            
        Returns:
            32-byte encryption key for Fernet
        """
        # Use Django's SECRET_KEY as the password
        password = settings.SECRET_KEY.encode('utf-8')
        salt = base64.b64decode(user_salt.encode('utf-8'))
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        
        return kdf.derive(password)
    
    def encrypt_key(self, key_value: str) -> None:
        """
        Encrypt and store API key value for retrieval.
        
        Args:
            key_value: Plain text API key to encrypt
        """
        if not key_value:
            raise ValueError("Key value cannot be empty")
            
        encryption_key = self._derive_encryption_key(self.salt)
        fernet = Fernet(base64.urlsafe_b64encode(encryption_key))
        
        encrypted_data = fernet.encrypt(key_value.encode('utf-8'))
        self.encrypted_key = base64.b64encode(encrypted_data).decode('utf-8')
        
        # Clear any existing hash when encrypting
        self.hashed_key = None
    
    def decrypt_key(self) -> Optional[str]:
        """
        Decrypt and return the API key value.
        
        Returns:
            Decrypted API key value or None if not encrypted
            
        Raises:
            ValueError: If decryption fails
        """
        if not self.encrypted_key:
            return None
            
        try:
            encryption_key = self._derive_encryption_key(self.salt)
            fernet = Fernet(base64.urlsafe_b64encode(encryption_key))
            
            encrypted_data = base64.b64decode(self.encrypted_key.encode('utf-8'))
            decrypted_data = fernet.decrypt(encrypted_data)
            
            return decrypted_data.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {str(e)}")
    
    def hash_key(self, key_value: str) -> None:
        """
        Hash API key value for verification-only storage.
        
        Args:
            key_value: Plain text API key to hash
        """
        if not key_value:
            raise ValueError("Key value cannot be empty")
            
        # Combine key with salt for hashing
        salted_key = f"{key_value}{self.salt}"
        
        # Use SHA-256 for hashing
        hash_obj = hashlib.sha256(salted_key.encode('utf-8'))
        self.hashed_key = hash_obj.hexdigest()
        
        # Clear any existing encryption when hashing
        self.encrypted_key = None
    
    def verify_key(self, key_value: str) -> bool:
        """
        Verify API key against stored hash.
        
        Args:
            key_value: Plain text API key to verify
            
        Returns:
            True if key matches hash, False otherwise
        """
        if not self.hashed_key or not key_value:
            return False
            
        # Hash the provided key with salt
        salted_key = f"{key_value}{self.salt}"
        hash_obj = hashlib.sha256(salted_key.encode('utf-8'))
        provided_hash = hash_obj.hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(self.hashed_key, provided_hash)
    
    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a cryptographically secure API key.
        
        Returns:
            Base64 encoded 32-byte random API key
        """
        return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
    
    class Meta:
        db_table = "api_keys"
        default_permissions = ()
        unique_together = [('user', 'name')]
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['last_used']),
        ]