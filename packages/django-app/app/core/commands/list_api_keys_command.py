from typing import Any, Dict, List

from common.commands.abstract_base_command import AbstractBaseCommand
from core.repositories import APIKeyRepository


class ListAPIKeysCommand(AbstractBaseCommand):
    """
    Command to list a user's API keys.
    """
    
    def __init__(
        self,
        user,
        active_only: bool = True,
    ) -> None:
        self.user = user
        self.active_only = active_only
    
    def execute(self) -> Dict[str, Any]:
        """
        List user's API keys.
        
        Returns:
            Dictionary containing list of API keys (without sensitive data)
        """
        api_keys = APIKeyRepository.get_user_api_keys(self.user, self.active_only)
        
        keys_data = []
        for api_key in api_keys:
            keys_data.append({
                'uuid': str(api_key.uuid),
                'name': api_key.name,
                'scope': api_key.scope,
                'is_active': api_key.is_active,
                'last_used': api_key.last_used.isoformat() if api_key.last_used else None,
                'last_used_ip': api_key.last_used_ip,
                'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
                'created_at': api_key.created_at.isoformat(),
                'updated_at': api_key.updated_at.isoformat(),
                'created_from_ip': api_key.created_from_ip,
                'storage_type': 'encrypted' if api_key.encrypted_key else 'hashed',
            })
        
        return {
            'api_keys': keys_data,
            'total_count': len(keys_data),
            'active_only': self.active_only,
        }