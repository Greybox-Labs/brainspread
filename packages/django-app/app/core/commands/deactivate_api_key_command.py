from typing import Any, Dict

from common.commands.abstract_base_command import AbstractBaseCommand
from core.repositories import APIKeyRepository, APIKeyAuditRepository


class DeactivateAPIKeyCommand(AbstractBaseCommand):
    """
    Command to deactivate an API key.
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
        Deactivate an API key.
        
        Returns:
            Dictionary containing the deactivated API key details
        """
        try:
            # Get the existing API key
            api_key = APIKeyRepository.get(pk=self.api_key_uuid)
            
            if not api_key:
                raise ValueError("API key not found")
            
            if api_key.user != self.user:
                raise ValueError("API key does not belong to this user")
            
            if not api_key.is_active:
                raise ValueError("API key is already inactive")
            
            # Deactivate the key
            APIKeyRepository.deactivate_key(api_key)
            
            # Log the deactivation
            APIKeyAuditRepository.model.log_operation(
                user=self.user,
                api_key=api_key,
                action='deactivated',
                ip_address=self.ip_address,
                user_agent=self.user_agent,
                details={'reason': 'manual_deactivation'}
            )
            
            return {
                'api_key': {
                    'uuid': str(api_key.uuid),
                    'name': api_key.name,
                    'scope': api_key.scope,
                    'is_active': api_key.is_active,
                    'updated_at': api_key.updated_at.isoformat(),
                },
                'message': 'API key deactivated successfully'
            }
            
        except Exception as e:
            # Log the failed deactivation attempt
            APIKeyAuditRepository.model.log_operation(
                user=self.user,
                api_key=None,
                action='deactivated',
                ip_address=self.ip_address,
                user_agent=self.user_agent,
                success=False,
                error_message=str(e),
                details={'api_key_uuid': self.api_key_uuid}
            )
            raise