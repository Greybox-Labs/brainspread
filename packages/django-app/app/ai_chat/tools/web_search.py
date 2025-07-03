from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class WebSearchConfig:
    """Configuration for web search tools"""

    max_uses: Optional[int] = None
    allowed_domains: Optional[List[str]] = None
    blocked_domains: Optional[List[str]] = None
    user_location: Optional[str] = None


class WebSearchTools:
    """Factory for creating web search tool configurations for different providers"""

    @staticmethod
    def anthropic_web_search(
        config: Optional[WebSearchConfig] = None,
    ) -> Dict[str, Any]:
        """Create Anthropic web search tool configuration"""
        tool_config = {"type": "web_search_20250305", "name": "web_search"}

        if config:
            if config.max_uses is not None:
                tool_config["max_uses"] = config.max_uses
            if config.allowed_domains:
                tool_config["allowed_domains"] = config.allowed_domains
            if config.blocked_domains:
                tool_config["blocked_domains"] = config.blocked_domains
            if config.user_location:
                tool_config["user_location"] = config.user_location

        return tool_config

    @staticmethod
    def openai_web_search() -> Dict[str, Any]:
        """Create OpenAI web search tool configuration for Responses API"""
        return {"type": "web_search_preview", "search_context_size": "medium"}

    @staticmethod
    def google_search() -> Dict[str, Any]:
        """Create Google Search grounding tool configuration"""
        return {"google_search": {}}

    @staticmethod
    def google_url_context() -> Dict[str, Any]:
        """Create Google URL context tool configuration"""
        return {"url_context": {}}
