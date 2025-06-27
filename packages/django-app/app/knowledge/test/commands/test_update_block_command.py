from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from knowledge.commands import CreateBlockCommand, UpdateBlockCommand
from knowledge.forms import CreateBlockForm, UpdateBlockForm
from knowledge.models import Block

from ..helpers import PageFactory, UserFactory, BlockFactory


class TestUpdateBlockCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.page = PageFactory(user=cls.user)
        cls.block = BlockFactory(page=cls.page, user=cls.user)

    def test_should_auto_detect_todo_when_content_changes_to_todo_prefix(self):
        """Test that updating content to 'TODO:' changes block type to todo"""
        form_data = {
            "user": self.user.id,
            "block": str(self.block.uuid),
            "content": "TODO: Buy groceries",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "todo")
        self.assertEqual(updated_block.content, "TODO: Buy groceries")

    def test_should_auto_detect_todo_when_content_changes_to_checkbox_empty(self):
        """Test that updating content to '[ ]' changes block type to todo"""
        form_data = {
            "user": self.user.id,
            "block": str(self.block.uuid),
            "content": "[ ] Complete project",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "todo")

    def test_should_auto_detect_done_when_content_changes_to_checkbox_checked(self):
        """Test that updating content to '[x]' changes block type to done"""
        form_data = {
            "user": self.user.id,
            "block": str(self.block.uuid),
            "content": "[x] Finished task",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "done")

    def test_should_auto_detect_done_when_content_changes_to_unicode_checkbox(self):
        """Test that updating content to '☑' changes block type to done"""
        form_data = {
            "user": self.user.id,
            "block": str(self.block.uuid),
            "content": "☑ Unicode done item",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "done")

    def test_should_change_from_todo_to_done_via_content_update(self):
        """Test changing from TODO to DONE by updating content"""
        # First create a todo block
        form_data = {
            "user": self.user.id,
            "page": self.page.uuid,
            "content": "TODO: Task to complete",
        }
        form = CreateBlockForm(form_data)
        form.is_valid()
        create_command = CreateBlockCommand(form)
        todo_block = create_command.execute()
        self.assertEqual(todo_block.block_type, "todo")

        # Then update content to mark as done
        form_data = {
            "user": self.user.id,
            "block": str(todo_block.uuid),
            "content": "[x] Task completed",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        update_command = UpdateBlockCommand(form)
        updated_block = update_command.execute()

        self.assertEqual(updated_block.block_type, "done")
        self.assertEqual(updated_block.content, "[x] Task completed")

    def test_should_not_override_heading_block_type(self):
        """Test that auto-detection doesn't override heading type"""
        # Create a heading block
        form_data = {
            "user": self.user.id,
            "page": self.page.uuid,
            "content": "# Heading",
            "block_type": "heading",
        }
        form = CreateBlockForm(form_data)
        form.is_valid()
        create_command = CreateBlockCommand(form)
        heading_block = create_command.execute()

        # Update content to TODO pattern - should NOT change type
        form_data = {
            "user": self.user.id,
            "block": str(heading_block.uuid),
            "content": "TODO: This should stay a heading",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "heading")

    def test_should_not_override_code_block_type(self):
        """Test that auto-detection doesn't override code type"""
        # Create a code block
        form_data = {
            "user": self.user.id,
            "page": self.page.uuid,
            "content": "console.log('hello')",
            "block_type": "code",
        }
        form = CreateBlockForm(form_data)
        form.is_valid()
        create_command = CreateBlockCommand(form)
        code_block = create_command.execute()

        # Update content to TODO pattern - should NOT change type
        form_data = {
            "user": self.user.id,
            "block": str(code_block.uuid),
            "content": "[ ] This should stay code",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "code")

    def test_should_preserve_block_type_when_no_pattern_matches(self):
        """Test that block type is preserved when content doesn't match patterns"""
        # Start with a todo block
        form_data = {
            "user": self.user.id,
            "page": self.page.uuid,
            "content": "TODO: Original task",
        }
        form = CreateBlockForm(form_data)
        form.is_valid()
        create_command = CreateBlockCommand(form)
        todo_block = create_command.execute()
        self.assertEqual(todo_block.block_type, "todo")

        # Update to regular content - should keep todo type
        form_data = {
            "user": self.user.id,
            "block": str(todo_block.uuid),
            "content": "Just regular content now",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "todo")

    def test_should_not_auto_detect_when_content_not_updated(self):
        """Test that auto-detection only happens when content is updated"""
        # Create a bullet block
        original_block = self.block

        # Update other field, not content
        form_data = {
            "user": self.user.id,
            "block": str(original_block.uuid),
            "order": 5,
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        # Block type should remain unchanged
        self.assertEqual(updated_block.block_type, "bullet")
        self.assertEqual(updated_block.order, 5)

    def test_should_handle_empty_content_update(self):
        """Test that updating to empty content preserves block type"""
        form_data = {
            "user": self.user.id,
            "block": str(self.block.uuid),
            "content": "",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "bullet")
        self.assertEqual(updated_block.content, "")

    def test_should_raise_validation_error_for_nonexistent_block(self):
        """Test that updating nonexistent block raises ValidationError"""
        form_data = {
            "user": self.user.id,
            "block": "nonexistent-uuid",
            "content": "New content",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)

        with self.assertRaises(ValidationError):
            command.execute()

    def test_should_be_case_insensitive_for_todo_detection(self):
        """Test that TODO detection is case insensitive in updates"""
        test_cases = [
            ("todo: lowercase", "todo"),
            ("TODO: uppercase", "todo"),
            ("Todo: mixed case", "todo"),
        ]

        for content, expected_type in test_cases:
            with self.subTest(content=content):
                form_data = {
                    "user": self.user.id,
                    "block": str(self.block.uuid),
                    "content": content,
                }
                form = UpdateBlockForm(form_data)
                form.is_valid()
                command = UpdateBlockCommand(form)
                updated_block = command.execute()
                self.assertEqual(updated_block.block_type, expected_type)

    @patch.object(Block, "set_tags_from_content")
    def test_should_call_set_tags_from_content_when_content_updated(
        self, mock_set_tags
    ):
        """Test that tags are extracted when content is updated"""
        form_data = {
            "user": self.user.id,
            "block": str(self.block.uuid),
            "content": "TODO: Buy #groceries and #food",
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        mock_set_tags.assert_called_once_with(
            "TODO: Buy #groceries and #food", self.user
        )

    @patch.object(Block, "set_tags_from_content")
    def test_should_not_call_set_tags_from_content_when_content_not_updated(
        self, mock_set_tags
    ):
        """Test that tag extraction is skipped when content isn't updated"""
        form_data = {
            "user": self.user.id,
            "block": str(self.block.uuid),
            "order": 10,
        }
        form = UpdateBlockForm(form_data)
        form.is_valid()
        command = UpdateBlockCommand(form)
        updated_block = command.execute()

        mock_set_tags.assert_not_called()
