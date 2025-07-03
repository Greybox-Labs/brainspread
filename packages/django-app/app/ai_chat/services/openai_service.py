import logging
from typing import Any, Dict, List, Optional

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

    def send_message(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Send messages to OpenAI API and return the response content.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            tools: Optional list of tools to make available to the model

        Returns:
            str: The assistant's response content

        Raises:
            OpenAIServiceError: If the API call fails
        """
        try:
            # Validate messages format using base class method
            self.validate_messages(messages)

            # Prepare API call parameters
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.7,
            }

            # Check if tools are provided - if so, use Responses API
            if tools:
                return self._send_message_with_responses_api(messages, tools)

            # Use regular Chat Completions API
            response: ChatCompletion = self.client.chat.completions.create(**kwargs)

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

    def _send_message_with_responses_api(
        self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]
    ) -> str:
        """
        Send message using OpenAI's Responses API for native web search

        Args:
            messages: List of message dictionaries
            tools: List of tools to use

        Returns:
            str: The assistant's response content
        """
        try:
            # Convert messages to a single input string for Responses API
            # Take the last user message as the input
            user_messages = [msg for msg in messages if msg["role"] == "user"]
            if not user_messages:
                raise OpenAIServiceError("No user messages found for Responses API")

            input_text = user_messages[-1]["content"]

            # Make the Responses API call with native web search
            response = self.client.responses.create(
                model=self.model, tools=tools, input=input_text
            )

            # Extract the text from the response
            if hasattr(response, "output_text") and response.output_text:
                return response.output_text
            elif hasattr(response, "output") and response.output:
                # Handle different response formats
                for item in response.output:
                    if hasattr(item, "type") and item.type == "message":
                        if hasattr(item, "content") and item.content:
                            for content_item in item.content:
                                if hasattr(content_item, "text"):
                                    return content_item.text

            raise OpenAIServiceError("No text content found in Responses API response")

        except AttributeError as e:
            if "'OpenAI' object has no attribute 'responses'" in str(e):
                logger.warning(
                    "OpenAI SDK version doesn't support Responses API, falling back to Chat Completions without web search"
                )
                return self._send_message_without_tools(messages)
            else:
                raise OpenAIServiceError(f"OpenAI Responses API error: {str(e)}") from e
        except Exception as e:
            logger.error(f"OpenAI Responses API error: {str(e)}")
            # Try to determine if it's a Responses API availability issue
            if any(
                keyword in str(e).lower()
                for keyword in ["responses", "not found", "unsupported"]
            ):
                logger.warning(
                    "Responses API not available, falling back to Chat Completions without web search"
                )
                return self._send_message_without_tools(messages)
            else:
                raise OpenAIServiceError(
                    f"OpenAI Responses API call failed: {str(e)}"
                ) from e

    def _send_message_without_tools(self, messages: List[Dict[str, str]]) -> str:
        """
        Send message using regular Chat Completions API without tools

        Args:
            messages: List of message dictionaries

        Returns:
            str: The assistant's response content
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.7,
        }

        response: ChatCompletion = self.client.chat.completions.create(**kwargs)

        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content:
                return content
            else:
                raise OpenAIServiceError("No content in OpenAI response")
        else:
            raise OpenAIServiceError("No choices in OpenAI response")
