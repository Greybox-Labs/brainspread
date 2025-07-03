from typing import Dict, List, Type

from .anthropic_service import AnthropicService
from .base_ai_service import AIServiceError, BaseAIService
from .google_service import GoogleService
from .openai_service import OpenAIService


class AIServiceFactoryError(AIServiceError):
    """Custom exception for AI service factory errors"""

    pass


class AIServiceFactory:
    """Factory class for creating AI service instances"""

    # Registry of available AI services
    _services: Dict[str, Type[BaseAIService]] = {
        "openai": OpenAIService,
        "anthropic": AnthropicService,
        "google": GoogleService,
    }

    @classmethod
    def create_service(
        cls, provider_name: str, api_key: str, model: str
    ) -> BaseAIService:
        """
        Create an AI service instance for the specified provider.

        Args:
            provider_name: Name of the AI provider (e.g., 'openai', 'anthropic')
            api_key: API key for the service
            model: Model name to use

        Returns:
            BaseAIService: Instance of the appropriate AI service

        Raises:
            AIServiceFactoryError: If provider is not supported
        """
        provider_key = provider_name.lower()

        if provider_key not in cls._services:
            supported = ", ".join(cls._services.keys())
            raise AIServiceFactoryError(
                f"Unsupported AI provider: {provider_name}. "
                f"Supported providers: {supported}"
            )

        service_class = cls._services[provider_key]
        return service_class(api_key=api_key, model=model)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """
        Get list of supported AI providers.

        Returns:
            List[str]: List of supported provider names
        """
        return list(cls._services.keys())

    @classmethod
    def register_service(
        cls, provider_name: str, service_class: Type[BaseAIService]
    ) -> None:
        """
        Register a new AI service provider.

        Args:
            provider_name: Name of the provider
            service_class: Class implementing BaseAIService
        """
        if not issubclass(service_class, BaseAIService):
            raise AIServiceFactoryError("Service class must inherit from BaseAIService")

        cls._services[provider_name.lower()] = service_class
