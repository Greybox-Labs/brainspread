from typing import Any, Dict, Optional
from django.utils import timezone

from common.commands.abstract_base_command import AbstractBaseCommand
from core.models import APIKey, APIKeyAudit
from core.repositories import APIKeyRepository, APIKeyAuditRepository


class VerifyAPIKeyCommand(AbstractBaseCommand):
    """
    Command to verify an API key and authenticate a user.
    """
    
    def __init__(
        self,
        key_value: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> None:
        self.key_value = key_value
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def execute(self) -> Dict[str, Any]:
        """
        Verify the API key and return user information if valid.
        
        Returns:
            Dictionary containing user info and key details if valid, or error info
        """
        try:
            # Find API keys that could match (both encrypted and hashed)
            # We need to check all active keys since we can't query encrypted/hashed fields directly
            potential_keys = APIKey.objects.filter(
                is_active=True
            ).select_related('user')
            
            matched_key = None
            
            for api_key in potential_keys:
                # Check if key is expired
                if api_key.expires_at and api_key.expires_at < timezone.now():
                    # Mark as expired and log
                    APIKeyRepository.deactivate_key(api_key)
                    APIKeyAuditRepository.model.log_operation(
                        user=api_key.user,
                        api_key=api_key,
                        action='expired',
                        ip_address=self.ip_address,
                        user_agent=self.user_agent,
                    )
                    continue
                
                # Try to verify against encrypted key
                if api_key.encrypted_key:
                    try:
                        decrypted_key = api_key.decrypt_key()
                        if decrypted_key == self.key_value:
                            matched_key = api_key
                            break
                    except Exception:
                        # Decryption failed, continue checking other keys
                        continue
                
                # Try to verify against hashed key
                if api_key.hashed_key:
                    if api_key.verify_key(self.key_value):
                        matched_key = api_key
                        break
            
            if not matched_key:
                # Log failed authentication attempt
                # We don't know which user this was intended for, so we'll log without user
                APIKeyAudit.objects.create(
                    user_id=None,
                    api_key=None,
                    api_key_name='Unknown',
                    action='failed_auth',
                    ip_address=self.ip_address,
                    user_agent=self.user_agent,
                    success=False,
                    error_message='Invalid API key',
                    details={'key_prefix': self.key_value[:8] + '...' if len(self.key_value) > 8 else '***'}
                )
                
                return {
                    'valid': False,
                    'error': 'Invalid API key',
                }
            
            # Update last used timestamp
            APIKeyRepository.update_last_used(matched_key, self.ip_address)
            
            # Log successful usage
            APIKeyAuditRepository.model.log_operation(
                user=matched_key.user,
                api_key=matched_key,
                action='used',
                ip_address=self.ip_address,
                user_agent=self.user_agent,
                details={'scope': matched_key.scope}
            )
            
            return {
                'valid': True,
                'user': {
                    'uuid': str(matched_key.user.uuid),
                    'email': matched_key.user.email,
                    'is_active': matched_key.user.is_active,
                },
                'api_key': {
                    'uuid': str(matched_key.uuid),
                    'name': matched_key.name,
                    'scope': matched_key.scope,
                    'last_used': matched_key.last_used.isoformat() if matched_key.last_used else None,
                    'expires_at': matched_key.expires_at.isoformat() if matched_key.expires_at else None,
                }
            }
            
        except Exception as e:
            # Log the error
            APIKeyAudit.objects.create(
                user_id=None,
                api_key=None,
                api_key_name='Unknown',
                action='failed_auth',
                ip_address=self.ip_address,
                user_agent=self.user_agent,
                success=False,
                error_message=str(e),
                details={'error_type': type(e).__name__}
            )
            
            return {
                'valid': False,
                'error': 'Authentication error',
            }