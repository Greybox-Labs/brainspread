from unittest.mock import Mock, patch

from django.test import TestCase

from ai_chat.services.ai_service_factory import AIServiceFactory, AIServiceFactoryError
from ai_chat.services.base_ai_service import AIServiceError
from ai_chat.services.user_settings_service import UserSettingsService
from ai_chat.test.helpers import (
    AnthropicProviderFactory,
    OpenAIProviderFactory,
    UserAISettingsFactory,
    UserProviderConfigFactory,
)
from core.test.helpers import UserFactory


class AIServiceFactoryTestCase(TestCase):
    """Test AI service factory functionality"""

    def test_get_supported_providers(self):
        """Test getting list of supported providers"""
        providers = AIServiceFactory.get_supported_providers()
        self.assertIn("openai", providers)
        self.assertIn("anthropic", providers)
        self.assertIsInstance(providers, list)

    def test_create_openai_service(self):
        """Test creating OpenAI service"""
        with patch.object(AIServiceFactory, "_services") as mock_services:
            mock_service_class = Mock()
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance
            mock_services.__getitem__.return_value = mock_service_class
            mock_services.__contains__.return_value = True

            service = AIServiceFactory.create_service(
                provider_name="openai", api_key="test-key", model="gpt-4"
            )

            self.assertEqual(service, mock_instance)
            mock_service_class.assert_called_once_with(
                api_key="test-key", model="gpt-4"
            )

    def test_create_anthropic_service(self):
        """Test creating Anthropic service"""
        with patch.object(AIServiceFactory, "_services") as mock_services:
            mock_service_class = Mock()
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance
            mock_services.__getitem__.return_value = mock_service_class
            mock_services.__contains__.return_value = True

            service = AIServiceFactory.create_service(
                provider_name="anthropic", api_key="test-key", model="claude-3-sonnet"
            )

            self.assertEqual(service, mock_instance)
            mock_service_class.assert_called_once_with(
                api_key="test-key", model="claude-3-sonnet"
            )

    def test_create_service_case_insensitive(self):
        """Test service creation is case insensitive"""
        with patch.object(AIServiceFactory, "_services") as mock_services:
            mock_service_class = Mock()
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance
            mock_services.__getitem__.return_value = mock_service_class
            mock_services.__contains__.return_value = True

            # Test different cases
            for provider_name in ["OpenAI", "OPENAI", "openai", "OpEnAi"]:
                service = AIServiceFactory.create_service(
                    provider_name=provider_name, api_key="test-key", model="gpt-4"
                )
                self.assertEqual(service, mock_instance)

    def test_create_service_unsupported_provider(self):
        """Test creating service with unsupported provider raises error"""
        with self.assertRaises(AIServiceFactoryError) as context:
            AIServiceFactory.create_service(
                provider_name="unsupported", api_key="test-key", model="test-model"
            )

        self.assertIn("Unsupported AI provider: unsupported", str(context.exception))
        self.assertIn("Supported providers:", str(context.exception))

    def test_get_available_models_openai(self):
        """Test getting available models for OpenAI"""
        with patch.object(AIServiceFactory, "_services") as mock_services:
            mock_service_class = Mock()
            mock_instance = Mock()
            mock_instance.get_available_models.return_value = ["gpt-4", "gpt-3.5-turbo"]
            mock_service_class.return_value = mock_instance
            mock_services.__getitem__.return_value = mock_service_class
            mock_services.__contains__.return_value = True

            models = AIServiceFactory.get_available_models("openai")
            self.assertEqual(models, ["gpt-4", "gpt-3.5-turbo"])
            mock_service_class.assert_called_once_with(api_key="dummy", model="dummy")
            mock_instance.get_available_models.assert_called_once()

    def test_get_available_models_anthropic(self):
        """Test getting available models for Anthropic"""
        with patch.object(AIServiceFactory, "_services") as mock_services:
            mock_service_class = Mock()
            mock_instance = Mock()
            mock_instance.get_available_models.return_value = [
                "claude-3-sonnet",
                "claude-3-haiku",
            ]
            mock_service_class.return_value = mock_instance
            mock_services.__getitem__.return_value = mock_service_class
            mock_services.__contains__.return_value = True

            models = AIServiceFactory.get_available_models("anthropic")
            self.assertEqual(models, ["claude-3-sonnet", "claude-3-haiku"])
            mock_service_class.assert_called_once_with(api_key="dummy", model="dummy")
            mock_instance.get_available_models.assert_called_once()

    def test_get_available_models_unsupported_provider(self):
        """Test getting models for unsupported provider returns empty list"""
        models = AIServiceFactory.get_available_models("unsupported")
        self.assertEqual(models, [])


class UserSettingsServiceTestCase(TestCase):
    """Test user settings service functionality"""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@example.com")
        cls.openai_provider = OpenAIProviderFactory()
        cls.anthropic_provider = AnthropicProviderFactory()

    def test_get_user_settings_exists(self):
        """Test getting existing user settings"""
        settings = UserAISettingsFactory(
            user=self.user, provider=self.openai_provider, default_model="gpt-4"
        )

        result = UserSettingsService.get_user_settings(self.user)
        self.assertEqual(result, settings)

    def test_get_user_settings_not_exists(self):
        """Test getting user settings when none exist"""
        result = UserSettingsService.get_user_settings(self.user)
        self.assertIsNone(result)

    def test_get_api_key_exists(self):
        """Test getting API key when provider config exists"""
        UserProviderConfigFactory(
            user=self.user, provider=self.openai_provider, api_key="test-api-key-123"
        )

        api_key = UserSettingsService.get_api_key(self.user, self.openai_provider)
        self.assertEqual(api_key, "test-api-key-123")

    def test_get_api_key_not_exists(self):
        """Test getting API key when provider config doesn't exist"""
        api_key = UserSettingsService.get_api_key(self.user, self.openai_provider)
        self.assertIsNone(api_key)

    def test_get_api_key_disabled_provider(self):
        """Test getting API key for disabled provider returns None"""
        UserProviderConfigFactory(
            user=self.user,
            provider=self.openai_provider,
            api_key="test-api-key-123",
            is_enabled=False,
        )

        api_key = UserSettingsService.get_api_key(self.user, self.openai_provider)
        self.assertIsNone(api_key)

    def test_get_api_key_empty_key(self):
        """Test getting empty API key returns None"""
        UserProviderConfigFactory(
            user=self.user, provider=self.openai_provider, api_key="", is_enabled=True
        )

        api_key = UserSettingsService.get_api_key(self.user, self.openai_provider)
        self.assertIsNone(api_key)

    def test_user_isolation(self):
        """Test that user settings are properly isolated"""
        # Create settings for test user
        test_settings = UserAISettingsFactory(
            user=self.user, provider=self.openai_provider
        )

        # Create settings for different user
        other_user = UserFactory(email="other@example.com")
        other_settings = UserAISettingsFactory(
            user=other_user, provider=self.anthropic_provider
        )

        # Verify isolation
        result = UserSettingsService.get_user_settings(self.user)
        self.assertEqual(result, test_settings)
        self.assertNotEqual(result, other_settings)

        result_other = UserSettingsService.get_user_settings(other_user)
        self.assertEqual(result_other, other_settings)
        self.assertNotEqual(result_other, test_settings)


class BaseAIServiceTestCase(TestCase):
    """Test base AI service functionality"""

    def test_ai_service_error_creation(self):
        """Test creating AI service error"""
        error = AIServiceError("Test error message")
        self.assertEqual(str(error), "Test error message")
        self.assertIsInstance(error, Exception)

    def test_ai_service_error_inheritance(self):
        """Test AI service error inheritance"""
        error = AIServiceError("Test error")
        self.assertIsInstance(error, Exception)

    @patch("ai_chat.services.openai_service.OpenAIService.send_message")
    def test_service_interface_compliance(self, mock_send_message):
        """Test that services comply with base interface"""
        mock_send_message.return_value = "Test response"

        # Test that we can create and use a service through the factory
        service = AIServiceFactory.create_service(
            provider_name="openai", api_key="test-key", model="gpt-4"
        )

        # Should have send_message method
        self.assertTrue(hasattr(service, "send_message"))

        # Test calling the method
        messages = [{"role": "user", "content": "Hello"}]
        response = service.send_message(messages)

        mock_send_message.assert_called_once_with(messages)
        self.assertEqual(response, "Test response")


class ServiceIntegrationTestCase(TestCase):
    """Test integration between services"""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@example.com")
        cls.openai_provider = OpenAIProviderFactory()

    def setUp(self):
        self.user_settings = UserAISettingsFactory(
            user=self.user, provider=self.openai_provider, default_model="gpt-4"
        )

        self.provider_config = UserProviderConfigFactory(
            user=self.user, provider=self.openai_provider, api_key="test-api-key-12345"
        )

    @patch("ai_chat.services.ai_service_factory.AIServiceFactory.create_service")
    def test_full_service_workflow(self, mock_create_service):
        """Test complete workflow from settings to service creation"""
        # Mock the service
        mock_service = Mock()
        mock_service.send_message.return_value = "AI response"
        mock_create_service.return_value = mock_service

        # Get user settings
        settings = UserSettingsService.get_user_settings(self.user)
        self.assertIsNotNone(settings)

        # Get API key
        api_key = UserSettingsService.get_api_key(self.user, settings.provider)
        self.assertEqual(api_key, "test-api-key-12345")

        # Create service
        service = AIServiceFactory.create_service(
            provider_name=settings.provider.name,
            api_key=api_key,
            model=settings.default_model,
        )

        # Send message
        messages = [{"role": "user", "content": "Hello"}]
        response = service.send_message(messages)

        # Verify workflow
        mock_create_service.assert_called_once_with(
            provider_name=self.openai_provider.name,
            api_key="test-api-key-12345",
            model="gpt-4",
        )
        mock_service.send_message.assert_called_once_with(messages)
        self.assertEqual(response, "AI response")

    def test_settings_without_provider_config(self):
        """Test that settings work but API key is None without provider config"""
        # Delete provider config
        self.provider_config.delete()

        # Get settings should still work
        settings = UserSettingsService.get_user_settings(self.user)
        self.assertIsNotNone(settings)

        # But API key should be None
        api_key = UserSettingsService.get_api_key(self.user, settings.provider)
        self.assertIsNone(api_key)

    def test_provider_config_without_settings(self):
        """Test that provider config exists but settings might not"""
        # Delete user settings but keep provider config
        self.user_settings.delete()

        # Settings should be None
        settings = UserSettingsService.get_user_settings(self.user)
        self.assertIsNone(settings)

        # But we can still get API key if we have the provider
        api_key = UserSettingsService.get_api_key(self.user, self.openai_provider)
        self.assertEqual(api_key, "test-api-key-12345")
