from django.test import TestCase
from unittest.mock import patch

from knowledge.commands import CreateBlockCommand
from knowledge.models import Block
from ..helpers import UserFactory, PageFactory


class TestCreateBlockCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.page = PageFactory(user=cls.user)

    def test_should_auto_detect_todo_from_todo_prefix(self):
        """Test that blocks starting with 'TODO' are created as todo type"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="TODO: Buy groceries",
        )
        block = command.execute()
        
        self.assertEqual(block.block_type, "todo")
        self.assertEqual(block.content, "TODO: Buy groceries")

    def test_should_auto_detect_todo_from_checkbox_empty(self):
        """Test that blocks starting with '[ ]' are created as todo type"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="[ ] Complete project",
        )
        block = command.execute()
        
        self.assertEqual(block.block_type, "todo")

    def test_should_auto_detect_done_from_checkbox_checked(self):
        """Test that blocks starting with '[x]' are created as done type"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="[x] Finished task",
        )
        block = command.execute()
        
        self.assertEqual(block.block_type, "done")

    def test_should_auto_detect_todo_from_unicode_checkbox(self):
        """Test that blocks starting with '☐' are created as todo type"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="☐ Unicode todo item",
        )
        block = command.execute()
        
        self.assertEqual(block.block_type, "todo")

    def test_should_auto_detect_done_from_unicode_checkbox(self):
        """Test that blocks starting with '☑' are created as done type"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="☑ Unicode done item",
        )
        block = command.execute()
        
        self.assertEqual(block.block_type, "done")

    def test_should_not_override_explicit_block_type(self):
        """Test that explicit block_type is not overridden by auto-detection"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="TODO: This should stay as heading",
            block_type="heading",
        )
        block = command.execute()
        
        self.assertEqual(block.block_type, "heading")

    def test_should_default_to_bullet_for_regular_content(self):
        """Test that regular content defaults to bullet type"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="Just a regular block",
        )
        block = command.execute()
        
        self.assertEqual(block.block_type, "bullet")

    def test_should_handle_empty_content(self):
        """Test that empty content defaults to bullet type"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="",
        )
        block = command.execute()
        
        self.assertEqual(block.block_type, "bullet")

    def test_should_handle_whitespace_only_content(self):
        """Test that whitespace-only content defaults to bullet type"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="   \n\t  ",
        )
        block = command.execute()
        
        self.assertEqual(block.block_type, "bullet")

    def test_should_be_case_insensitive_for_todo_detection(self):
        """Test that TODO detection is case insensitive"""
        test_cases = [
            "todo: lowercase",
            "TODO: uppercase", 
            "Todo: mixed case",
            "tOdO: weird case",
        ]
        
        for content in test_cases:
            with self.subTest(content=content):
                command = CreateBlockCommand(
                    user=self.user,
                    page=self.page,
                    content=content,
                )
                block = command.execute()
                self.assertEqual(block.block_type, "todo")

    @patch.object(Block, "set_tags_from_content")
    def test_should_call_set_tags_from_content_when_content_exists(self, mock_set_tags):
        """Test that tags are extracted from block content"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="TODO: Buy #groceries and #food",
        )
        block = command.execute()
        
        mock_set_tags.assert_called_once_with("TODO: Buy #groceries and #food", self.user)

    @patch.object(Block, "set_tags_from_content")
    def test_should_not_call_set_tags_from_content_when_no_content(self, mock_set_tags):
        """Test that tag extraction is skipped for empty content"""
        command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="",
        )
        block = command.execute()
        
        mock_set_tags.assert_not_called()