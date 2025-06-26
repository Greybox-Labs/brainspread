from typing import Optional

from ai_chat.models import UserAISettings, UserProviderConfig
from common.repositories.base_repository import BaseRepository


class UserSettingsRepository(BaseRepository):
    """Repository for user AI settings data access"""

    def get_user_settings(self, user) -> Optional[UserAISettings]:
        """
        Get AI settings for a user.

        Args:
            user: The user object

        Returns:
            UserAISettings or None if not configured
        """
        try:
            return UserAISettings.objects.get(user=user)
        except UserAISettings.DoesNotExist:
            return None

    def has_valid_settings(self, user) -> bool:
        """
        Check if user has valid AI settings configured.

        Args:
            user: The user object

        Returns:
            bool: True if user has preferred model and at least one API key configured
        """
        settings = self.get_user_settings(user)
        if not settings or not settings.preferred_model:
            return False

        # Check if user has at least one API key configured
        provider_configs = UserProviderConfig.objects.filter(
            user=user, is_enabled=True
        ).exclude(api_key__isnull=True).exclude(api_key__exact='')
        
        return provider_configs.exists()

    def get_api_key(self, user, provider) -> Optional[str]:
        """
        Get API key for a user and provider.

        Args:
            user: The user object
            provider: The AI provider object

        Returns:
            str or None: The API key if configured
        """
        try:
            provider_config = UserProviderConfig.objects.get(
                user=user, provider=provider
            )
            if provider_config.is_enabled and provider_config.api_key:
                return provider_config.api_key
            return None
        except UserProviderConfig.DoesNotExist:
            return None
