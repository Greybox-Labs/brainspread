import logging
from typing import Dict, List

from common.commands.abstract_base_command import AbstractBaseCommand

from ai_chat.repositories.chat_repository import ChatRepository
from ai_chat.services.openai_service import OpenAIService, OpenAIServiceError
from ai_chat.services.user_settings_service import UserSettingsService

logger = logging.getLogger(__name__)


class SendMessageCommandError(Exception):
    """Custom exception for command errors"""
    pass


class SendMessageCommand(AbstractBaseCommand):
    def __init__(self, user, session, message: str) -> None:
        self.user = user
        self.session = session
        self.message = message

    def execute(self) -> Dict[str, str]:
        super().execute()

        try:
            # Get user's AI settings
            user_settings = UserSettingsService.get_user_settings(self.user)
            
            if not user_settings:
                raise SendMessageCommandError(
                    "No AI settings configured. Please configure your AI provider and API key in settings."
                )
            
            # Check if settings are complete
            if not user_settings.provider:
                raise SendMessageCommandError("No AI provider configured.")
            
            if not user_settings.api_key:
                raise SendMessageCommandError("No API key configured.")
            
            api_key = user_settings.api_key
            
            if not user_settings.default_model:
                raise SendMessageCommandError("No default model configured.")
            
            # Validate provider (currently only OpenAI is supported)
            if user_settings.provider.name.lower() != "openai":
                raise SendMessageCommandError(
                    f"Provider '{user_settings.provider.name}' is not currently supported. "
                    "Please configure OpenAI as your provider."
                )

            # Create or get session
            if not self.session:
                self.session = ChatRepository.create_session(self.user)

            # Add user message to database
            ChatRepository.add_message(self.session, "user", self.message)

            # Get conversation history
            messages: List[Dict[str, str]] = [
                {"role": msg.role, "content": msg.content}
                for msg in ChatRepository.get_messages(self.session)
            ]

            # Call OpenAI service
            service = OpenAIService(api_key, user_settings.default_model)
            response_content = service.send_message(messages)

            # Add assistant response to database
            ChatRepository.add_message(self.session, "assistant", response_content)

            return {
                "response": response_content,
                "session_id": str(self.session.uuid)
            }

        except OpenAIServiceError as e:
            logger.error(f"OpenAI service error for user {self.user.id}: {str(e)}")
            # Still save the user message even if AI fails
            if self.session:
                ChatRepository.add_message(self.session, "assistant", 
                                         f"Sorry, I'm experiencing technical difficulties: {str(e)}")
            raise SendMessageCommandError(f"AI service error: {str(e)}") from e
        
        except SendMessageCommandError:
            # Re-raise command errors as-is
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error in SendMessageCommand for user {self.user.id}: {str(e)}")
            raise SendMessageCommandError(f"An unexpected error occurred: {str(e)}") from e
