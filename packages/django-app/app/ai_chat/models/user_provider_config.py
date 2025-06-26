from typing import Optional

from django.conf import settings
from django.db import models

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin
from common.security.encryption import APIKeyEncryption

from .ai_provider import AIProvider


class UserProviderConfig(UUIDModelMixin, CRUDTimestampsMixin):
    """Stores user configuration for each AI provider with encrypted API keys."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE)
    
    # Encrypted API key storage
    encrypted_api_key = models.TextField(blank=True, help_text="Encrypted API key data")
    api_key_salt = models.CharField(max_length=255, blank=True, help_text="Salt for API key encryption")
    
    # Optional: hash-only storage for verification-only keys
    api_key_hash = models.CharField(max_length=255, blank=True, help_text="Hashed API key for verification")
    api_key_hash_salt = models.CharField(max_length=255, blank=True, help_text="Salt for API key hash")
    
    # Legacy field - keep for migration compatibility
    api_key = models.CharField(max_length=255, blank=True, help_text="Legacy plain text field - deprecated")
    
    is_enabled = models.BooleanField(default=True)
    enabled_models = models.ManyToManyField(
        "AIModel",
        blank=True,
        help_text="Models that this user has enabled for this provider",
    )

    class Meta:
        db_table = "user_provider_configs"
        unique_together = [("user", "provider")]
        indexes = [
            models.Index(fields=['user', 'provider']),
            models.Index(fields=['is_enabled']),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.provider.name}"

    def set_api_key(self, api_key: str, hash_only: bool = False) -> bool:
        """
        Set the API key using encryption or hashing.
        
        Args:
            api_key: The plaintext API key to store
            hash_only: If True, store only a hash for verification (can't decrypt)
            
        Returns:
            True if successful, False otherwise
        """
        if not api_key:
            self.clear_api_key()
            return True
            
        try:
            if hash_only:
                # Store only hash for verification
                api_key_hash, salt = APIKeyEncryption.hash_api_key_for_verification(
                    api_key, self.user.id
                )
                self.api_key_hash = api_key_hash
                self.api_key_hash_salt = salt
                self.encrypted_api_key = ""
                self.api_key_salt = ""
            else:
                # Store encrypted version that can be decrypted
                encrypted_data, salt = APIKeyEncryption.encrypt_api_key(
                    api_key, self.user.id
                )
                self.encrypted_api_key = encrypted_data
                self.api_key_salt = salt
                self.api_key_hash = ""
                self.api_key_hash_salt = ""
            
            # Clear legacy field
            self.api_key = ""
            return True
            
        except Exception:
            return False

    def get_api_key(self) -> Optional[str]:
        """
        Get the decrypted API key.
        
        Returns:
            The decrypted API key or None if not available/decryptable
        """
        # Handle legacy plain text keys first
        if self.api_key:
            return self.api_key
            
        # Try to decrypt if we have encrypted data
        if self.encrypted_api_key and self.api_key_salt:
            return APIKeyEncryption.decrypt_api_key(
                self.encrypted_api_key, self.api_key_salt, self.user.id
            )
            
        return None

    def verify_api_key(self, api_key: str) -> bool:
        """
        Verify an API key against stored hash.
        Use this for hash-only storage or verification.
        
        Args:
            api_key: The plaintext API key to verify
            
        Returns:
            True if the key matches
        """
        if self.api_key_hash and self.api_key_hash_salt:
            return APIKeyEncryption.verify_api_key_hash(
                api_key, self.api_key_hash, self.api_key_hash_salt, self.user.id
            )
        
        # Fallback: compare with decrypted key
        stored_key = self.get_api_key()
        return stored_key == api_key if stored_key else False

    def has_api_key(self) -> bool:
        """Check if this config has an API key configured."""
        return bool(
            self.api_key or  # Legacy
            (self.encrypted_api_key and self.api_key_salt) or  # Encrypted
            (self.api_key_hash and self.api_key_hash_salt)  # Hash-only
        )

    def clear_api_key(self) -> None:
        """Clear all API key data."""
        self.api_key = ""
        self.encrypted_api_key = ""
        self.api_key_salt = ""
        self.api_key_hash = ""
        self.api_key_hash_salt = ""
