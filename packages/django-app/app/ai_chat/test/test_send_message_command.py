from unittest.mock import Mock, patch
from django.test import TestCase

from core.test.helpers import UserFactory
from ai_chat.commands.send_message import SendMessageCommand, SendMessageCommandError
from ai_chat.models import ChatSession, ChatMessage
from ai_chat.services.base_ai_service import AIServiceError
from ai_chat.services.ai_service_factory import AIServiceFactoryError

from .helpers import (
    UserAISettingsFactory,
    UserProviderConfigFactory,
    ChatSessionFactory,
    ChatMessageFactory,
    OpenAIProviderFactory,
)


class SendMessageCommandTestCase(TestCase):
    """Test SendMessageCommand with mocked AI services"""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@example.com")
        cls.openai_provider = OpenAIProviderFactory()

    def setUp(self):
        # Create user AI settings with OpenAI as default
        self.user_settings = UserAISettingsFactory(
            user=self.user,
            provider=self.openai_provider,
            default_model="gpt-4"
        )
        
        # Create provider config with API key
        self.provider_config = UserProviderConfigFactory(
            user=self.user,
            provider=self.openai_provider,
            api_key="test-api-key-12345",
            enabled_models=["gpt-4", "gpt-3.5-turbo"]
        )

    @patch('ai_chat.services.ai_service_factory.AIServiceFactory.create_service')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.create_session')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.add_message')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.get_messages')
    def test_execute_success_new_session(self, mock_get_messages, mock_add_message, 
                                       mock_create_session, mock_create_service):
        """Test successful command execution with new session"""
        # Setup mocks
        mock_session = Mock()
        mock_session.uuid = "test-session-uuid"
        mock_create_session.return_value = mock_session
        
        mock_message = Mock()
        mock_message.role = "user"
        mock_message.content = "Hello, AI!"
        mock_get_messages.return_value = [mock_message]
        
        mock_service = Mock()
        mock_service.send_message.return_value = "Hello! How can I help you?"
        mock_create_service.return_value = mock_service

        # Execute command
        command = SendMessageCommand(
            user=self.user,
            session=None,  # No existing session
            message="Hello, AI!",
            context_blocks=[]
        )
        result = command.execute()

        # Verify result
        self.assertEqual(result["response"], "Hello! How can I help you?")
        self.assertEqual(result["session_id"], "test-session-uuid")

        # Verify mocks were called correctly
        mock_create_session.assert_called_once_with(self.user)
        self.assertEqual(mock_add_message.call_count, 2)  # User message + AI response
        mock_create_service.assert_called_once_with(
            provider_name=self.openai_provider.name,
            api_key="test-api-key-12345",
            model="gpt-4"
        )
        mock_service.send_message.assert_called_once_with([{
            "role": "user",
            "content": "Hello, AI!"
        }])

    @patch('ai_chat.services.ai_service_factory.AIServiceFactory.create_service')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.add_message')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.get_messages')
    def test_execute_success_existing_session(self, mock_get_messages, mock_add_message, 
                                            mock_create_service):
        """Test successful command execution with existing session"""
        # Create existing session
        session = ChatSessionFactory(user=self.user)
        
        # Setup mocks
        mock_messages = [
            Mock(role="user", content="Previous message"),
            Mock(role="assistant", content="Previous response"),
        ]
        mock_get_messages.return_value = mock_messages
        
        mock_service = Mock()
        mock_service.send_message.return_value = "Follow-up response"
        mock_create_service.return_value = mock_service

        # Execute command
        command = SendMessageCommand(
            user=self.user,
            session=session,
            message="Follow-up question",
            context_blocks=[]
        )
        result = command.execute()

        # Verify result
        self.assertEqual(result["response"], "Follow-up response")
        self.assertEqual(result["session_id"], str(session.uuid))

        # Verify conversation history was passed to AI service
        expected_messages = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"},
            {"role": "user", "content": "Follow-up question"},
        ]
        mock_service.send_message.assert_called_once()
        call_args = mock_service.send_message.call_args[0][0]
        self.assertEqual(len(call_args), 3)  # Previous 2 + new user message

    def test_execute_no_settings_error(self):
        """Test command fails when no AI settings configured"""
        # Delete user settings
        self.user_settings.delete()

        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="Hello",
            context_blocks=[]
        )

        with self.assertRaises(SendMessageCommandError) as context:
            command.execute()

        self.assertIn("No AI settings configured", str(context.exception))

    def test_execute_no_provider_error(self):
        """Test command fails when no provider configured"""
        # Remove provider from settings
        self.user_settings.provider = None
        self.user_settings.save()

        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="Hello",
            context_blocks=[]
        )

        with self.assertRaises(SendMessageCommandError) as context:
            command.execute()

        self.assertIn("No AI provider configured", str(context.exception))

    def test_execute_no_api_key_error(self):
        """Test command fails when no API key configured"""
        # Delete provider config (which contains API key)
        self.provider_config.delete()

        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="Hello",
            context_blocks=[]
        )

        with self.assertRaises(SendMessageCommandError) as context:
            command.execute()

        self.assertIn("No API key configured", str(context.exception))

    def test_execute_no_model_error(self):
        """Test command fails when no default model configured"""
        # Remove default model
        self.user_settings.default_model = None
        self.user_settings.save()

        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="Hello",
            context_blocks=[]
        )

        with self.assertRaises(SendMessageCommandError) as context:
            command.execute()

        self.assertIn("No default model configured", str(context.exception))

    @patch('ai_chat.services.ai_service_factory.AIServiceFactory.get_supported_providers')
    def test_execute_unsupported_provider_error(self, mock_get_providers):
        """Test command fails when provider is not supported"""
        mock_get_providers.return_value = ["openai", "anthropic"]
        
        # Change provider to unsupported one
        unsupported_provider = OpenAIProviderFactory(name="UnsupportedProvider")
        self.user_settings.provider = unsupported_provider
        self.user_settings.save()

        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="Hello",
            context_blocks=[]
        )

        with self.assertRaises(SendMessageCommandError) as context:
            command.execute()

        self.assertIn("Provider 'UnsupportedProvider' is not supported", str(context.exception))

    @patch('ai_chat.services.ai_service_factory.AIServiceFactory.create_service')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.create_session')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.add_message')
    def test_execute_ai_service_error(self, mock_add_message, mock_create_session, 
                                    mock_create_service):
        """Test command handles AI service errors gracefully"""
        # Setup mocks
        mock_session = Mock()
        mock_session.uuid = "test-session-uuid"
        mock_create_session.return_value = mock_session
        
        # Make AI service fail
        mock_create_service.side_effect = AIServiceError("API rate limit exceeded")

        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="Hello",
            context_blocks=[]
        )

        with self.assertRaises(SendMessageCommandError) as context:
            command.execute()

        self.assertIn("AI service error", str(context.exception))
        
        # Verify error message was added to session
        mock_add_message.assert_called_with(
            mock_session,
            "assistant",
            "Sorry, I'm experiencing technical difficulties: API rate limit exceeded"
        )

    @patch('ai_chat.services.ai_service_factory.AIServiceFactory.create_service')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.create_session')
    def test_execute_service_factory_error(self, mock_create_session, mock_create_service):
        """Test command handles service factory errors"""
        # Setup mocks
        mock_session = Mock()
        mock_create_session.return_value = mock_session
        
        # Make service factory fail
        mock_create_service.side_effect = AIServiceFactoryError("Unsupported provider")

        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="Hello",
            context_blocks=[]
        )

        with self.assertRaises(SendMessageCommandError) as context:
            command.execute()

        self.assertIn("AI service error", str(context.exception))

    def test_format_message_with_context_blocks(self):
        """Test message formatting with context blocks"""
        context_blocks = [
            {"content": "Buy groceries", "block_type": "todo"},
            {"content": "Call dentist", "block_type": "done"},
            {"content": "Regular note", "block_type": "bullet"},
            {"content": "Heading note", "block_type": "heading"},
        ]

        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="What should I do?",
            context_blocks=context_blocks
        )

        formatted_message = command._format_message_with_context()

        # Verify context formatting
        self.assertIn("**Context from my notes:**", formatted_message)
        self.assertIn("☐ Buy groceries", formatted_message)
        self.assertIn("☑ Call dentist", formatted_message)
        self.assertIn("• Regular note", formatted_message)
        self.assertIn("• Heading note", formatted_message)  # Default to bullet
        self.assertIn("**My question:**", formatted_message)
        self.assertIn("What should I do?", formatted_message)

    def test_format_message_no_context_blocks(self):
        """Test message formatting without context blocks"""
        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="Simple question",
            context_blocks=[]
        )

        formatted_message = command._format_message_with_context()
        self.assertEqual(formatted_message, "Simple question")

    def test_format_message_empty_context_blocks(self):
        """Test message formatting with empty context blocks"""
        context_blocks = [
            {"content": "", "block_type": "todo"},
            {"content": "   ", "block_type": "bullet"},
        ]

        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="Question with empty context",
            context_blocks=context_blocks
        )

        formatted_message = command._format_message_with_context()
        self.assertEqual(formatted_message, "Question with empty context")

    @patch('ai_chat.services.ai_service_factory.AIServiceFactory.create_service')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.create_session')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.add_message')
    @patch('ai_chat.repositories.chat_repository.ChatRepository.get_messages')
    def test_execute_with_context_blocks_integration(self, mock_get_messages, mock_add_message,
                                                   mock_create_session, mock_create_service):
        """Test full execution with context blocks"""
        # Setup mocks
        mock_session = Mock()
        mock_session.uuid = "test-session-uuid"
        mock_create_session.return_value = mock_session
        
        # The formatted message will be captured by get_messages
        mock_message = Mock()
        mock_message.role = "user"
        mock_message.content = "**Context from my notes:**\n☐ Important task\n\n**My question:**\nWhat to do?"
        mock_get_messages.return_value = [mock_message]
        
        mock_service = Mock()
        mock_service.send_message.return_value = "Based on your notes, here's what I suggest..."
        mock_create_service.return_value = mock_service

        # Execute command with context blocks
        command = SendMessageCommand(
            user=self.user,
            session=None,
            message="What to do?",
            context_blocks=[{"content": "Important task", "block_type": "todo"}]
        )
        result = command.execute()

        # Verify result
        self.assertEqual(result["response"], "Based on your notes, here's what I suggest...")
        
        # Verify the user message was formatted with context
        user_message_call = mock_add_message.call_args_list[0]
        formatted_content = user_message_call[0][2]  # Third argument is content
        self.assertIn("**Context from my notes:**", formatted_content)
        self.assertIn("☐ Important task", formatted_content)