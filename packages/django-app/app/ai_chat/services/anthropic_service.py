import logging
from typing import Dict, List

import anthropic

from .base_ai_service import AIServiceError, BaseAIService

logger = logging.getLogger(__name__)


class AnthropicServiceError(AIServiceError):
    """Custom exception for Anthropic service errors"""

    pass


class AnthropicService(BaseAIService):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        super().__init__(api_key, model)
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise AnthropicServiceError(
                f"Failed to initialize Anthropic client: {e}"
            ) from e

    def send_message(self, messages: List[Dict[str, str]]) -> str:
        """
        Send messages to Anthropic API and return the response content.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys

        Returns:
            str: The assistant's response content

        Raises:
            AnthropicServiceError: If the API call fails
        """
        try:
            # Validate messages format using base class method
            self.validate_messages(messages)

            # Convert messages format for Anthropic API
            anthropic_messages = []
            system_message = None

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append(
                        {"role": msg["role"], "content": msg["content"]}
                    )

            # Prepare API call parameters
            kwargs = {
                "model": self.model,
                "max_tokens": 2000,
                "messages": anthropic_messages,
            }

            # Add system message if present
            if system_message:
                kwargs["system"] = system_message

            # Make the API call
            response = self.client.messages.create(**kwargs)

            # Extract the content from the response
            if response.content and len(response.content) > 0:
                content = response.content[0].text
                if content:
                    return content
                else:
                    raise AnthropicServiceError("No content in Anthropic response")
            else:
                raise AnthropicServiceError("No content blocks in Anthropic response")

        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            if isinstance(e, AnthropicServiceError):
                raise
            else:
                raise AnthropicServiceError(
                    f"Anthropic API call failed: {str(e)}"
                ) from e

    def get_available_models(self) -> List[str]:
        """
        Get list of available Anthropic models.

        Returns:
            List[str]: List of available model names
        """
        return [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def validate_api_key(self) -> bool:
        """
        Validate the Anthropic API key by making a test call.

        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            # Make a minimal test call to validate the API key
            test_messages = [{"role": "user", "content": "Hi"}]
            response = self.client.messages.create(
                model=self.model, max_tokens=1, messages=test_messages
            )
            return response is not None
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
