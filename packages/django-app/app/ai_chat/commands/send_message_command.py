import logging
from typing import Any, Dict, List, Optional

from ai_chat.services.ai_service_factory import AIServiceFactory, AIServiceFactoryError
from ai_chat.services.base_ai_service import AIServiceError
from ai_chat.tools.web_search import WebSearchTools
from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms import SendMessageForm
from ..repositories import (
    AIModelRepository,
    ChatMessageRepository,
    ChatSessionRepository,
)

logger = logging.getLogger(__name__)


class SendMessageCommandError(Exception):
    """Custom exception for command errors"""

    pass


class SendMessageCommand(AbstractBaseCommand):
    def __init__(self, form: SendMessageForm) -> None:
        self.form = form

    def execute(self) -> Dict[str, str]:
        super().execute()

        try:
            # Get validated data from form
            message = self.form.cleaned_data["message"]
            model = self.form.cleaned_data["model"]
            session = self.form.cleaned_data.get("session_id")
            context_blocks = self.form.cleaned_data.get("context_blocks", [])
            provider_name = self.form.cleaned_data["provider_name"]
            api_key = self.form.cleaned_data["api_key"]
            user = self.form.cleaned_data["user"]

            # Create or get session
            if not session:
                session = ChatSessionRepository.create_session(user)

            # Prepare the message with context blocks
            formatted_message = self._format_message_with_context(
                message, context_blocks
            )

            # Add user message to database
            ChatMessageRepository.add_message(session, "user", formatted_message)

            # Get conversation history
            messages: List[Dict[str, str]] = [
                {"role": msg.role, "content": msg.content}
                for msg in ChatMessageRepository.get_messages(session)
            ]

            # Create AI service using factory
            service = AIServiceFactory.create_service(
                provider_name=provider_name,
                api_key=api_key,
                model=model,
            )
            # Configure web search tools if enabled
            tools = self._get_web_search_tools(provider_name)

            response_content = service.send_message(messages, tools)

            # Get the AI model to store with the assistant response
            ai_model = AIModelRepository.get_by_name(model)

            # Add assistant response to database
            assistant_message = ChatMessageRepository.add_message(
                session, "assistant", response_content, ai_model
            )

            # Return complete message data including AI model info
            return {
                "response": response_content,
                "session_id": str(session.uuid),
                "message": {
                    "role": assistant_message.role,
                    "content": assistant_message.content,
                    "created_at": assistant_message.created_at.isoformat(),
                    "ai_model": (
                        {
                            "name": ai_model.name,
                            "display_name": ai_model.display_name,
                            "provider": ai_model.provider.name,
                        }
                        if ai_model
                        else None
                    ),
                },
            }

        except (AIServiceError, AIServiceFactoryError) as e:
            logger.error(f"AI service error for user {user.id}: {str(e)}")
            # Still save the user message even if AI fails
            if session:
                ai_model = AIModelRepository.get_by_name(model)
                error_message = (
                    f"Sorry, I'm experiencing technical difficulties: {str(e)}"
                )
                assistant_message = ChatMessageRepository.add_message(
                    session,
                    "assistant",
                    error_message,
                    ai_model,
                )
            raise SendMessageCommandError(f"AI service error: {str(e)}") from e

        except SendMessageCommandError:
            # Re-raise command errors as-is
            raise

        except Exception as e:
            logger.error(
                f"Unexpected error in SendMessageCommand for user {user.id}: {str(e)}"
            )
            raise SendMessageCommandError(
                f"An unexpected error occurred: {str(e)}"
            ) from e

    def _format_message_with_context(
        self, message: str, context_blocks: List[Dict]
    ) -> str:
        """Format the user message with context blocks if any are provided."""
        if not context_blocks:
            return message

        # Format context blocks
        context_text_parts = []
        for block in context_blocks:
            content = block.get("content", "").strip()
            if content:
                block_type = block.get("block_type", "bullet")
                if block_type == "todo":
                    context_text_parts.append(f"☐ {content}")
                elif block_type == "done":
                    context_text_parts.append(f"☑ {content}")
                else:
                    context_text_parts.append(f"• {content}")

        if not context_text_parts:
            return message

        # Combine context and message
        context_section = "\n".join(context_text_parts)
        formatted_message = f"""**Context from my notes:**
{context_section}

**My question:**
{message}"""

        return formatted_message

    def _get_web_search_tools(
        self, provider_name: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get web search tools configuration for the specified provider."""
        # Enable web search for all providers
        if provider_name == "anthropic":
            return [WebSearchTools.anthropic_web_search()]
        elif provider_name == "openai":
            return [WebSearchTools.openai_web_search()]
        elif provider_name == "google":
            return [WebSearchTools.google_search()]

        return None
