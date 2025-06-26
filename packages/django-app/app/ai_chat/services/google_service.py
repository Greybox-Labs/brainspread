import logging
from typing import Dict, List

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .base_ai_service import AIServiceError, BaseAIService

logger = logging.getLogger(__name__)


class GoogleServiceError(AIServiceError):
    """Google AI service specific error"""

    pass


class GoogleService(BaseAIService):
    """Google AI (Gemini) service implementation"""

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

    def send_message(self, messages: List[Dict[str, str]]) -> str:
        """
        Send messages to Google AI service and return the response content.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys

        Returns:
            str: The assistant's response content

        Raises:
            GoogleServiceError: If the API call fails
        """
        try:
            self.validate_messages(messages)

            # Convert messages to Google AI format
            formatted_messages = self._format_messages_for_google(messages)

            # Generate response
            response = self.client.generate_content(formatted_messages)

            if not response.text:
                raise GoogleServiceError("Empty response from Google AI")

            return response.text

        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Google AI API error: {e}")
            raise GoogleServiceError(f"Google AI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Google AI service: {e}")
            raise GoogleServiceError(f"Unexpected error: {e}")

    def get_available_models(self) -> List[str]:
        """
        Get list of available Gemini models.
        Ordered by capability and performance.

        Returns:
            List[str]: List of available model names
        """
        return [
            "gemini-2.5-pro",  # Most advanced model - best for complex tasks
            "gemini-2.5-flash-preview",  # Latest fast model with advanced capabilities
            "gemini-2.0-pro",  # High-end model for complex reasoning
            "gemini-2.0-flash",  # Balanced performance and speed
            "gemini-1.5-pro",  # Proven reliable model
            "gemini-1.5-flash",  # Fast and efficient
            "gemini-1.5-flash-8b",  # Lightweight model for simple tasks
        ]

    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a test call.

        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            # Use a reliable model for validation
            test_model = genai.GenerativeModel("gemini-1.5-flash")
            response = test_model.generate_content("Hi")  # Minimal test prompt
            return response.text is not None
        except google_exceptions.GoogleAPIError:
            return False
        except Exception:
            return False

    def _format_messages_for_google(self, messages: List[Dict[str, str]]) -> str:
        """
        Format messages for Google AI API.

        Google AI expects a single text prompt, so we'll concatenate messages
        with role indicators.

        Args:
            messages: List of message dictionaries

        Returns:
            str: Formatted prompt for Google AI
        """
        formatted_parts = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                formatted_parts.append(f"System: {content}")
            elif role == "user":
                formatted_parts.append(f"User: {content}")
            elif role == "assistant":
                formatted_parts.append(f"Assistant: {content}")

        return "\n\n".join(formatted_parts)
