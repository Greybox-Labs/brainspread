from typing import Optional

from ai_chat.models import UserAISettings


class UserSettingsService:
    """Service to manage user AI settings"""
    
    @staticmethod
    def get_user_settings(user) -> Optional[UserAISettings]:
        """
        Get AI settings for a user.
        
        Args:
            user: The user object
            
        Returns:
            UserAISettings or None if not configured
        """
        try:
            return UserAISettings.objects.select_related('provider').get(user=user)
        except UserAISettings.DoesNotExist:
            return None
    
    @staticmethod
    def has_valid_settings(user) -> bool:
        """
        Check if user has valid AI settings configured.
        
        Args:
            user: The user object
            
        Returns:
            bool: True if user has provider, model, and API key configured
        """
        settings = UserSettingsService.get_user_settings(user)
        return (settings is not None and 
                settings.provider is not None and 
                settings.api_key and 
                settings.default_model)