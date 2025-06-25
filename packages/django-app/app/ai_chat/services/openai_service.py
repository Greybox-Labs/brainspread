import logging
from typing import List, Dict

from openai import OpenAI
from openai.types.chat import ChatCompletion

logger = logging.getLogger(__name__)


class OpenAIServiceError(Exception):
    """Custom exception for OpenAI service errors"""
    pass


class OpenAIService:
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
            # Validate messages format
            for msg in messages:
                if "role" not in msg or "content" not in msg:
                    raise OpenAIServiceError("Invalid message format: missing 'role' or 'content'")
                if msg["role"] not in ["user", "assistant", "system"]:
                    raise OpenAIServiceError(f"Invalid role: {msg['role']}")

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
