import logging
from typing import Dict, List

from ai_chat.repositories.chat_repository import ChatRepository
from ai_chat.services.ai_service_factory import AIServiceFactory, AIServiceFactoryError
from ai_chat.services.base_ai_service import AIServiceError
from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms import SendMessageForm

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
            user = self.form.user

            # Create or get session
            if not session:
                session = ChatRepository.create_session(user)

            # Prepare the message with context blocks
            formatted_message = self._format_message_with_context(
                message, context_blocks
            )

            # Add user message to database
            ChatRepository.add_message(session, "user", formatted_message)

            # Get conversation history
            messages: List[Dict[str, str]] = [
                {"role": msg.role, "content": msg.content}
                for msg in ChatRepository.get_messages(session)
            ]

            # Create AI service using factory
            service = AIServiceFactory.create_service(
                provider_name=provider_name,
                api_key=api_key,
                model=model,
            )
            response_content = service.send_message(messages)

            # Add assistant response to database
            ChatRepository.add_message(session, "assistant", response_content)

            return {"response": response_content, "session_id": str(session.uuid)}

        except (AIServiceError, AIServiceFactoryError) as e:
            logger.error(f"AI service error for user {user.id}: {str(e)}")
            # Still save the user message even if AI fails
            if session:
                ChatRepository.add_message(
                    session,
                    "assistant",
                    f"Sorry, I'm experiencing technical difficulties: {str(e)}",
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
