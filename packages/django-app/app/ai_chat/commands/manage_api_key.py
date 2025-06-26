"""Commands for managing API keys with audit logging."""
from typing import Optional

from django.contrib.auth import get_user_model
from django.http import HttpRequest

from ai_chat.models import AIProvider, APIKeyAudit, UserProviderConfig

User = get_user_model()


class ManageAPIKeyCommand:
    """Command for managing user API keys with security and audit logging."""

    def __init__(self, request: Optional[HttpRequest] = None):
        """
        Initialize command with optional request for audit metadata.
        
        Args:
            request: HTTP request for extracting IP and user agent
        """
        self.request = request

    def _log_operation(
        self,
        user: User,
        provider: AIProvider,
        operation: str,
        success: bool = True,
        error_message: str = "",
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Log API key operation for audit trail.
        
        Args:
            user: The user performing the operation
            provider: The AI provider
            operation: The operation type
            success: Whether the operation succeeded
            error_message: Error message if failed
            metadata: Additional metadata to store
        """
        ip_address = None
        user_agent = ""
        
        if self.request:
            # Extract IP address (handle forwarded headers)
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = self.request.META.get('REMOTE_ADDR')
            
            user_agent = self.request.META.get('HTTP_USER_AGENT', '')

        APIKeyAudit.objects.create(
            user=user,
            provider=provider,
            operation=operation,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            success=success,
            error_message=error_message,
        )

    def set_api_key(
        self,
        user: User,
        provider: AIProvider,
        api_key: str,
        hash_only: bool = False,
    ) -> tuple[bool, str]:
        """
        Set or update an API key for a user and provider.
        
        Args:
            user: The user
            provider: The AI provider
            api_key: The plaintext API key
            hash_only: Whether to store only a hash (verification-only)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get or create config
            config, created = UserProviderConfig.objects.get_or_create(
                user=user,
                provider=provider,
                defaults={'is_enabled': True}
            )
            
            # Check if key already exists for update detection
            had_key = config.has_api_key()
            
            # Set the API key
            success = config.set_api_key(api_key, hash_only=hash_only)
            
            if not success:
                self._log_operation(
                    user, provider, APIKeyAudit.OperationType.CREATED if created else APIKeyAudit.OperationType.UPDATED,
                    success=False, error_message="Failed to encrypt API key"
                )
                return False, "Failed to encrypt API key"
            
            # Save the config
            config.save()
            
            # Log the operation
            operation = APIKeyAudit.OperationType.CREATED if (created or not had_key) else APIKeyAudit.OperationType.UPDATED
            self._log_operation(
                user, provider, operation,
                metadata={
                    'hash_only': hash_only,
                    'key_length': len(api_key),
                    'created_new_config': created,
                }
            )
            
            return True, "API key saved successfully"
            
        except Exception as e:
            self._log_operation(
                user, provider, APIKeyAudit.OperationType.CREATED,
                success=False, error_message=str(e)
            )
            return False, f"Error saving API key: {str(e)}"

    def get_api_key(self, user: User, provider: AIProvider) -> tuple[Optional[str], bool]:
        """
        Get decrypted API key for a user and provider.
        
        Args:
            user: The user
            provider: The AI provider
            
        Returns:
            Tuple of (api_key, success)
        """
        try:
            config = UserProviderConfig.objects.get(
                user=user, 
                provider=provider,
                is_enabled=True
            )
            
            if not config.has_api_key():
                self._log_operation(
                    user, provider, APIKeyAudit.OperationType.FAILED_ACCESS,
                    success=False, error_message="No API key configured"
                )
                return None, False
            
            api_key = config.get_api_key()
            
            if api_key is None:
                self._log_operation(
                    user, provider, APIKeyAudit.OperationType.FAILED_ACCESS,
                    success=False, error_message="Failed to decrypt API key"
                )
                return None, False
            
            # Log successful access
            self._log_operation(
                user, provider, APIKeyAudit.OperationType.ACCESSED,
                metadata={'key_length': len(api_key)}
            )
            
            return api_key, True
            
        except UserProviderConfig.DoesNotExist:
            self._log_operation(
                user, provider, APIKeyAudit.OperationType.FAILED_ACCESS,
                success=False, error_message="Provider config not found"
            )
            return None, False
        except Exception as e:
            self._log_operation(
                user, provider, APIKeyAudit.OperationType.FAILED_ACCESS,
                success=False, error_message=str(e)
            )
            return None, False

    def verify_api_key(self, user: User, provider: AIProvider, api_key: str) -> bool:
        """
        Verify an API key against stored data.
        
        Args:
            user: The user
            provider: The AI provider
            api_key: The API key to verify
            
        Returns:
            True if the key is valid
        """
        try:
            config = UserProviderConfig.objects.get(
                user=user, 
                provider=provider,
                is_enabled=True
            )
            
            if not config.has_api_key():
                self._log_operation(
                    user, provider, APIKeyAudit.OperationType.FAILED_ACCESS,
                    success=False, error_message="No API key to verify against"
                )
                return False
            
            is_valid = config.verify_api_key(api_key)
            
            # Log verification attempt
            operation = APIKeyAudit.OperationType.ACCESSED if is_valid else APIKeyAudit.OperationType.FAILED_ACCESS
            self._log_operation(
                user, provider, operation,
                success=is_valid,
                error_message="Invalid API key" if not is_valid else "",
                metadata={'verification_attempt': True}
            )
            
            return is_valid
            
        except UserProviderConfig.DoesNotExist:
            self._log_operation(
                user, provider, APIKeyAudit.OperationType.FAILED_ACCESS,
                success=False, error_message="Provider config not found for verification"
            )
            return False
        except Exception as e:
            self._log_operation(
                user, provider, APIKeyAudit.OperationType.FAILED_ACCESS,
                success=False, error_message=f"Verification error: {str(e)}"
            )
            return False

    def delete_api_key(self, user: User, provider: AIProvider) -> tuple[bool, str]:
        """
        Delete API key for a user and provider.
        
        Args:
            user: The user
            provider: The AI provider
            
        Returns:
            Tuple of (success, message)
        """
        try:
            config = UserProviderConfig.objects.get(
                user=user, 
                provider=provider
            )
            
            if not config.has_api_key():
                return True, "No API key to delete"
            
            # Clear the API key
            config.clear_api_key()
            config.save()
            
            # Log the operation
            self._log_operation(
                user, provider, APIKeyAudit.OperationType.DELETED
            )
            
            return True, "API key deleted successfully"
            
        except UserProviderConfig.DoesNotExist:
            return True, "No configuration found to delete"
        except Exception as e:
            self._log_operation(
                user, provider, APIKeyAudit.OperationType.DELETED,
                success=False, error_message=str(e)
            )
            return False, f"Error deleting API key: {str(e)}"

    def rotate_api_key(
        self,
        user: User,
        provider: AIProvider,
        new_api_key: str,
        hash_only: bool = False,
    ) -> tuple[bool, str]:
        """
        Rotate an existing API key.
        
        Args:
            user: The user
            provider: The AI provider
            new_api_key: The new API key
            hash_only: Whether to store only a hash
            
        Returns:
            Tuple of (success, message)
        """
        try:
            config = UserProviderConfig.objects.get(
                user=user, 
                provider=provider
            )
            
            if not config.has_api_key():
                return self.set_api_key(user, provider, new_api_key, hash_only)
            
            # Update with new key
            success = config.set_api_key(new_api_key, hash_only=hash_only)
            
            if not success:
                self._log_operation(
                    user, provider, APIKeyAudit.OperationType.UPDATED,
                    success=False, error_message="Failed to encrypt new API key during rotation"
                )
                return False, "Failed to encrypt new API key"
            
            config.save()
            
            # Log the rotation
            self._log_operation(
                user, provider, APIKeyAudit.OperationType.UPDATED,
                metadata={
                    'rotation': True,
                    'hash_only': hash_only,
                    'key_length': len(new_api_key),
                }
            )
            
            return True, "API key rotated successfully"
            
        except UserProviderConfig.DoesNotExist:
            return self.set_api_key(user, provider, new_api_key, hash_only)
        except Exception as e:
            self._log_operation(
                user, provider, APIKeyAudit.OperationType.UPDATED,
                success=False, error_message=f"Rotation error: {str(e)}"
            )
            return False, f"Error rotating API key: {str(e)}"