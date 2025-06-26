from typing import Optional

from ai_chat.models import UserAISettings, UserProviderConfig


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
            return UserAISettings.objects.select_related("provider").get(user=user)
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
        if not settings or not settings.provider or not settings.default_model:
            return False

        # Check if user has API key configured for the current provider
        try:
            provider_config = UserProviderConfig.objects.get(
                user=user, provider=settings.provider
            )
            return bool(provider_config.api_key and provider_config.is_enabled)
        except UserProviderConfig.DoesNotExist:
            # No provider config found
            return False

    @staticmethod
    def get_api_key(user, provider) -> Optional[str]:
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
            # No provider config found
            return None
