import pytest
from unittest.mock import AsyncMock, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model

from knowledge.models import Page
from mcp_server.tools.page_tools import PageTools
from mcp_server.utils.auth import get_current_user


User = get_user_model()


class PageToolsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        # Mock server
        self.mock_server = MagicMock()
        self.page_tools = PageTools(self.mock_server)
    
    def test_page_tools_initialization(self):
        """Test that PageTools initializes correctly"""
        self.assertIsNotNone(self.page_tools)
        self.assertEqual(self.page_tools.server, self.mock_server)
    
    def test_register_tools_called(self):
        """Test that register_tools can be called without errors"""
        # This will register the tools with the mock server
        try:
            self.page_tools.register_tools()
        except Exception as e:
            self.fail(f"register_tools() raised {e} unexpectedly!")
    
    @pytest.mark.asyncio
    async def test_create_page_basic_structure(self):
        """Test that create_page function has the right structure"""
        # This test just verifies the basic structure exists
        # More detailed testing would require actual MCP server setup
        self.page_tools.register_tools()
        
        # Verify that list_tools and call_tool decorators were called
        self.assertTrue(self.mock_server.list_tools.called)
        self.assertTrue(self.mock_server.call_tool.called)