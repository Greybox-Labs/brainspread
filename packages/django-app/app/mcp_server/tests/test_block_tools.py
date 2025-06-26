import pytest
from unittest.mock import MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model

from knowledge.models import Page, Block
from mcp_server.tools.block_tools import BlockTools


User = get_user_model()


class BlockToolsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.page = Page.objects.create(
            user=self.user,
            title="Test Page",
            slug="test-page"
        )
        # Mock server
        self.mock_server = MagicMock()
        self.block_tools = BlockTools(self.mock_server)
    
    def test_block_tools_initialization(self):
        """Test that BlockTools initializes correctly"""
        self.assertIsNotNone(self.block_tools)
        self.assertEqual(self.block_tools.server, self.mock_server)
    
    def test_register_tools_called(self):
        """Test that register_tools can be called without errors"""
        try:
            self.block_tools.register_tools()
        except Exception as e:
            self.fail(f"register_tools() raised {e} unexpectedly!")
    
    @pytest.mark.asyncio
    async def test_block_operations_structure(self):
        """Test that block operation functions have the right structure"""
        self.block_tools.register_tools()
        
        # Verify that decorators were called
        self.assertTrue(self.mock_server.list_tools.called)
        self.assertTrue(self.mock_server.call_tool.called)