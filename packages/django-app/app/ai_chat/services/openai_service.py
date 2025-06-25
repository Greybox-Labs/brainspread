import logging
from typing import Dict, List

from openai import OpenAI
from openai.types.chat import ChatCompletion

from .base_ai_service import AIServiceError, BaseAIService

logger = logging.getLogger(__name__)


class OpenAIServiceError(AIServiceError):
    """Custom exception for OpenAI service errors"""

    pass


class OpenAIService(BaseAIService):
    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self.api_key = api_key
        self.model = model
        # Initialize OpenAI client with minimal parameters to avoid proxy issues
        try:
            # Try with just the API key first
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise OpenAIServiceError(f"Failed to initialize OpenAI client: {e}") from e

    def send_message(self, messages: List[Dict[str, str]]) -> str:
        """
        Send messages to OpenAI API and return the response content.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys

        Returns:
            str: The assistant's response content

        Raises:
            OpenAIServiceError: If the API call fails
        """
        try:
            # Validate messages format using base class method
            self.validate_messages(messages)

            # Make the API call
            response: ChatCompletion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.7,
            )

            # Extract the content from the response
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return content
                else:
                    raise OpenAIServiceError("No content in OpenAI response")
            else:
                raise OpenAIServiceError("No choices in OpenAI response")

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            if isinstance(e, OpenAIServiceError):
                raise
            else:
                raise OpenAIServiceError(f"OpenAI API call failed: {str(e)}") from e

    def get_available_models(self) -> List[str]:
        """
        Get list of available OpenAI models.

        Returns:
            List[str]: List of available model names
        """
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]

    def validate_api_key(self) -> bool:
        """
        Validate the OpenAI API key by making a test call.

        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            # Make a minimal test call to validate the API key
            test_messages = [{"role": "user", "content": "Hi"}]
            response = self.client.chat.completions.create(
                model=self.model, messages=test_messages, max_tokens=1
            )
            return response is not None
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
