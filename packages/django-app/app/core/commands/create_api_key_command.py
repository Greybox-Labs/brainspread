from typing import Any, Dict, Optional

from common.commands.abstract_base_command import AbstractBaseCommand
from core.models import APIKey, APIKeyAudit
from core.repositories import APIKeyRepository, APIKeyAuditRepository


class CreateAPIKeyCommand(AbstractBaseCommand):
    """
    Command to create a new encrypted or hashed API key for a user.
    """
    
    def __init__(
        self,
        user,
        name: str,
        scope: str = 'read',
        expires_at = None,
        store_encrypted: bool = True,
        ip_address: str = None,
        user_agent: str = None,
    ) -> None:
        self.user = user
        self.name = name
        self.scope = scope
        self.expires_at = expires_at
        self.store_encrypted = store_encrypted
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def execute(self) -> Dict[str, Any]:
        """
        Create a new API key with encryption or hashing.
        
        Returns:
            Dictionary containing the new API key details and the generated key value
        """
        try:
            # Check if user already has a key with this name
            existing_key = APIKeyRepository.get_active_key_by_name(self.user, self.name)
            if existing_key:
                raise ValueError(f"API key with name '{self.name}' already exists")
            
            # Generate the API key value
            key_value = APIKey.generate_api_key()
            
            # Create the API key instance
            api_key = APIKey.objects.create(
                user=self.user,
                name=self.name,
                scope=self.scope,
                expires_at=self.expires_at,
                created_from_ip=self.ip_address,
            )
            
            # Store the key value (encrypted or hashed)
            if self.store_encrypted:
                api_key.encrypt_key(key_value)
            else:
                api_key.hash_key(key_value)
            
            api_key.save()
            
            # Log the creation
            APIKeyAuditRepository.model.log_operation(
                user=self.user,
                api_key=api_key,
                action='created',
                ip_address=self.ip_address,
                user_agent=self.user_agent,
                details={
                    'scope': self.scope,
                    'storage_type': 'encrypted' if self.store_encrypted else 'hashed',
                    'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                }
            )
            
            return {
                'api_key': {
                    'uuid': str(api_key.uuid),
                    'name': api_key.name,
                    'scope': api_key.scope,
                    'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
                    'created_at': api_key.created_at.isoformat(),
                },
                'key_value': key_value,  # Only returned once during creation
                'storage_type': 'encrypted' if self.store_encrypted else 'hashed',
            }
            
        except Exception as e:
            # Log the failed creation attempt
            APIKeyAuditRepository.model.log_operation(
                user=self.user,
                api_key=None,
                action='created',
                ip_address=self.ip_address,
                user_agent=self.user_agent,
                success=False,
                error_message=str(e),
                details={
                    'name': self.name,
                    'scope': self.scope,
                }
            )
            raise