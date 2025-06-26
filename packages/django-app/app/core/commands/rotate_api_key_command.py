from typing import Any, Dict

from common.commands.abstract_base_command import AbstractBaseCommand
from core.models import APIKey
from core.repositories import APIKeyRepository, APIKeyAuditRepository


class RotateAPIKeyCommand(AbstractBaseCommand):
    """
    Command to rotate (regenerate) an existing API key.
    """
    
    def __init__(
        self,
        user,
        api_key_uuid: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> None:
        self.user = user
        self.api_key_uuid = api_key_uuid
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def execute(self) -> Dict[str, Any]:
        """
        Rotate an existing API key by generating a new key value.
        
        Returns:
            Dictionary containing the updated API key details and new key value
        """
        try:
            # Get the existing API key
            api_key = APIKeyRepository.get(pk=self.api_key_uuid)
            
            if not api_key:
                raise ValueError("API key not found")
            
            if api_key.user != self.user:
                raise ValueError("API key does not belong to this user")
            
            if not api_key.is_active:
                raise ValueError("Cannot rotate inactive API key")
            
            # Generate new key value
            new_key_value = APIKey.generate_api_key()
            
            # Determine storage type from existing key
            was_encrypted = bool(api_key.encrypted_key)
            
            # Update the key with new value
            if was_encrypted:
                api_key.encrypt_key(new_key_value)
            else:
                api_key.hash_key(new_key_value)
            
            api_key.save()
            
            # Log the rotation
            APIKeyAuditRepository.model.log_operation(
                user=self.user,
                api_key=api_key,
                action='rotated',
                ip_address=self.ip_address,
                user_agent=self.user_agent,
                details={
                    'storage_type': 'encrypted' if was_encrypted else 'hashed',
                }
            )
            
            return {
                'api_key': {
                    'uuid': str(api_key.uuid),
                    'name': api_key.name,
                    'scope': api_key.scope,
                    'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
                    'updated_at': api_key.updated_at.isoformat(),
                },
                'new_key_value': new_key_value,  # Only returned once during rotation
                'storage_type': 'encrypted' if was_encrypted else 'hashed',
            }
            
        except Exception as e:
            # Log the failed rotation attempt
            APIKeyAuditRepository.model.log_operation(
                user=self.user,
                api_key=None,
                action='rotated',
                ip_address=self.ip_address,
                user_agent=self.user_agent,
                success=False,
                error_message=str(e),
                details={'api_key_uuid': self.api_key_uuid}
            )
            raise