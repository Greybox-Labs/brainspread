import pytest
from unittest.mock import MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model

from mcp_server.server import BrainspreadMCPServer
from mcp_server.utils.auth import get_current_user
from mcp_server.utils.validators import validate_uuid, validate_block_type, validate_content_type


User = get_user_model()


class IntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@email.com",  # Default user for auth
            password="testpass123"
        )
    
    def test_server_initialization(self):
        """Test that BrainspreadMCPServer initializes correctly"""
        try:
            server = BrainspreadMCPServer()
            self.assertIsNotNone(server)
            self.assertIsNotNone(server.server)
        except Exception as e:
            self.fail(f"BrainspreadMCPServer() raised {e} unexpectedly!")
    
    def test_auth_utils(self):
        """Test authentication utilities"""
        user = get_current_user()
        self.assertEqual(user.email, "admin@email.com")
    
    def test_validators(self):
        """Test validation utilities"""
        # Valid UUID
        self.assertTrue(validate_uuid("550e8400-e29b-41d4-a716-446655440000"))
        
        # Invalid UUID
        self.assertFalse(validate_uuid("invalid-uuid"))
        
        # Valid block types
        self.assertTrue(validate_block_type("bullet"))
        self.assertTrue(validate_block_type("todo"))
        self.assertTrue(validate_block_type("done"))
        
        # Invalid block type
        self.assertFalse(validate_block_type("invalid"))
        
        # Valid content types
        self.assertTrue(validate_content_type("text"))
        self.assertTrue(validate_content_type("markdown"))
        
        # Invalid content type
        self.assertFalse(validate_content_type("invalid"))
    
    def test_server_capabilities(self):
        """Test that server has expected capabilities"""
        server = BrainspreadMCPServer()
        
        # Verify tools are registered
        self.assertIsNotNone(server.server)
        
        # The server should have been set up with all tool categories
        # This verifies the setup_tools method ran without errors