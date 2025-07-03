from ai_chat.tools.web_search import WebSearchConfig, WebSearchTools


class TestWebSearchTools:
    """Test web search tool configurations"""

    def test_anthropic_web_search_basic(self):
        """Test basic Anthropic web search tool configuration"""
        tool = WebSearchTools.anthropic_web_search()

        assert tool["type"] == "web_search_20250305"
        assert tool["name"] == "web_search"
        assert "max_uses" not in tool
        assert "allowed_domains" not in tool
        assert "blocked_domains" not in tool
        assert "user_location" not in tool

    def test_anthropic_web_search_with_config(self):
        """Test Anthropic web search with custom configuration"""
        config = WebSearchConfig(
            max_uses=5,
            allowed_domains=["example.com", "test.org"],
            blocked_domains=["spam.com"],
            user_location="New York, NY",
        )

        tool = WebSearchTools.anthropic_web_search(config)

        assert tool["type"] == "web_search_20250305"
        assert tool["name"] == "web_search"
        assert tool["max_uses"] == 5
        assert tool["allowed_domains"] == ["example.com", "test.org"]
        assert tool["blocked_domains"] == ["spam.com"]
        assert tool["user_location"] == "New York, NY"

    def test_openai_web_search(self):
        """Test OpenAI web search tool configuration"""
        tool = WebSearchTools.openai_web_search()

        assert tool["type"] == "web_search_preview"

    def test_google_search(self):
        """Test Google Search grounding tool configuration"""
        tool = WebSearchTools.google_search()

        assert "google_search" in tool
        assert tool["google_search"] == {}

    def test_google_url_context(self):
        """Test Google URL context tool configuration"""
        tool = WebSearchTools.google_url_context()

        assert "url_context" in tool
        assert tool["url_context"] == {}


class TestWebSearchConfig:
    """Test web search configuration dataclass"""

    def test_web_search_config_defaults(self):
        """Test WebSearchConfig with default values"""
        config = WebSearchConfig()

        assert config.max_uses is None
        assert config.allowed_domains is None
        assert config.blocked_domains is None
        assert config.user_location is None

    def test_web_search_config_with_values(self):
        """Test WebSearchConfig with custom values"""
        config = WebSearchConfig(
            max_uses=10,
            allowed_domains=["domain1.com", "domain2.org"],
            blocked_domains=["blocked.com"],
            user_location="San Francisco, CA",
        )

        assert config.max_uses == 10
        assert config.allowed_domains == ["domain1.com", "domain2.org"]
        assert config.blocked_domains == ["blocked.com"]
        assert config.user_location == "San Francisco, CA"
