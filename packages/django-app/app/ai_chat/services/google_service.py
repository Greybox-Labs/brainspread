import logging
from typing import Any, Dict, List, Optional

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

    def send_message(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Send messages to Google AI service and return the response content.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            tools: Optional list of tools to make available to the model

        Returns:
            str: The assistant's response content

        Raises:
            GoogleServiceError: If the API call fails
        """
        try:
            self.validate_messages(messages)

            # Configure generation with tools if provided
            tool_config = None

            if tools:
                # Convert tools to Google AI format
                google_tools = self._convert_tools_to_google_format(tools)
                tool_config = google_tools

            # Convert messages to Google AI format
            formatted_messages = self._format_messages_for_google(messages)

            # Generate response
            if tool_config:
                try:
                    # Try direct tools parameter first
                    response = self.client.generate_content(
                        formatted_messages, tools=tool_config
                    )
                except google_exceptions.GoogleAPIError as e:
                    if (
                        "Search Grounding is not supported" in str(e)
                        or "not supported" in str(e).lower()
                    ):
                        logger.warning(
                            f"Google Search Grounding not supported, falling back to regular generation: {e}"
                        )
                        # Fallback to regular generation without tools
                        response = self.client.generate_content(formatted_messages)
                    else:
                        raise e
                except Exception as e:
                    logger.warning(
                        f"Google Search tool failed, falling back to regular generation: {e}"
                    )
                    response = self.client.generate_content(formatted_messages)
            else:
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

    def _convert_tools_to_google_format(
        self, tools: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Convert tools to Google AI format.

        Args:
            tools: List of tool configurations

        Returns:
            Optional[List[Dict[str, Any]]]: Tools in Google AI format, or None if not supported
        """
        try:
            google_tools = []

            for tool in tools:
                if "google_search" in tool:
                    # Try different formats for Google Search grounding
                    try:
                        # Method 1: Try the direct dictionary format
                        google_search_tool = {"google_search_retrieval": {}}
                        google_tools.append(google_search_tool)
                        logger.info(
                            "Google Search grounding tool added (dictionary format)"
                        )
                    except Exception as e:
                        logger.warning(f"Google Search grounding method 1 failed: {e}")
                        try:
                            # Method 2: Try alternative format
                            google_search_tool = {"google_search": {}}
                            google_tools.append(google_search_tool)
                            logger.info(
                                "Google Search grounding tool added (alternative format)"
                            )
                        except Exception as e2:
                            logger.warning(
                                f"Google Search grounding method 2 failed: {e2}"
                            )
                            continue
                elif "url_context" in tool:
                    # Handle URL context if needed
                    logger.info("URL context tool not implemented yet")
                    continue

            return google_tools if google_tools else None

        except Exception as e:
            logger.warning(f"Google tools conversion failed: {e}")
            return None
