from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AIServiceError(Exception):
    """Base exception for AI service errors"""

    pass


class BaseAIService(ABC):
    """Abstract base class for AI service implementations"""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def send_message(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Send messages to AI service and return the response content.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            tools: Optional list of tools/functions to make available to the model

        Returns:
            str: The assistant's response content

        Raises:
            AIServiceError: If the API call fails
        """
        pass

    @abstractmethod
    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a test call.

        Returns:
            bool: True if API key is valid, False otherwise
        """
        pass

    def validate_messages(self, messages: List[Dict[str, str]]) -> None:
        """
        Validate message format before sending to AI service.

        Args:
            messages: List of message dictionaries

        Raises:
            AIServiceError: If message format is invalid
        """
        for msg in messages:
            if "role" not in msg or "content" not in msg:
                raise AIServiceError(
                    "Invalid message format: missing 'role' or 'content'"
                )
            if msg["role"] not in ["user", "assistant", "system"]:
                raise AIServiceError(f"Invalid role: {msg['role']}")
