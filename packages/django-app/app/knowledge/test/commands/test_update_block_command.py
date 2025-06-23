from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch

from knowledge.commands import UpdateBlockCommand, CreateBlockCommand
from knowledge.models import Block
from ..helpers import UserFactory, PageFactory


class TestUpdateBlockCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.page = PageFactory(user=cls.user)

    def setUp(self):
        # Create a test block for updating
        create_command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="Original content",
            block_type="bullet",
        )
        self.block = create_command.execute()

    def test_should_auto_detect_todo_when_content_changes_to_todo_prefix(self):
        """Test that updating content to 'TODO:' changes block type to todo"""
        command = UpdateBlockCommand(
            user=self.user, block_id=self.block.uuid, content="TODO: Buy groceries"
        )
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "todo")
        self.assertEqual(updated_block.content, "TODO: Buy groceries")

    def test_should_auto_detect_todo_when_content_changes_to_checkbox_empty(self):
        """Test that updating content to '[ ]' changes block type to todo"""
        command = UpdateBlockCommand(
            user=self.user, block_id=self.block.uuid, content="[ ] Complete project"
        )
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "todo")

    def test_should_auto_detect_done_when_content_changes_to_checkbox_checked(self):
        """Test that updating content to '[x]' changes block type to done"""
        command = UpdateBlockCommand(
            user=self.user, block_id=self.block.uuid, content="[x] Finished task"
        )
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "done")

    def test_should_auto_detect_done_when_content_changes_to_unicode_checkbox(self):
        """Test that updating content to '☑' changes block type to done"""
        command = UpdateBlockCommand(
            user=self.user, block_id=self.block.uuid, content="☑ Unicode done item"
        )
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "done")

    def test_should_change_from_todo_to_done_via_content_update(self):
        """Test changing from TODO to DONE by updating content"""
        # First create a todo block
        create_command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="TODO: Task to complete",
        )
        todo_block = create_command.execute()
        self.assertEqual(todo_block.block_type, "todo")

        # Then update content to mark as done
        update_command = UpdateBlockCommand(
            user=self.user, block_id=todo_block.uuid, content="[x] Task completed"
        )
        updated_block = update_command.execute()

        self.assertEqual(updated_block.block_type, "done")
        self.assertEqual(updated_block.content, "[x] Task completed")

    def test_should_not_override_heading_block_type(self):
        """Test that auto-detection doesn't override heading type"""
        # Create a heading block
        create_command = CreateBlockCommand(
            user=self.user, page=self.page, content="# Heading", block_type="heading"
        )
        heading_block = create_command.execute()

        # Update content to TODO pattern - should NOT change type
        command = UpdateBlockCommand(
            user=self.user,
            block_id=heading_block.uuid,
            content="TODO: This should stay a heading",
        )
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "heading")

    def test_should_not_override_code_block_type(self):
        """Test that auto-detection doesn't override code type"""
        # Create a code block
        create_command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="console.log('hello')",
            block_type="code",
        )
        code_block = create_command.execute()

        # Update content to TODO pattern - should NOT change type
        command = UpdateBlockCommand(
            user=self.user,
            block_id=code_block.uuid,
            content="[ ] This should stay code",
        )
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "code")

    def test_should_preserve_block_type_when_no_pattern_matches(self):
        """Test that block type is preserved when content doesn't match patterns"""
        # Start with a todo block
        create_command = CreateBlockCommand(
            user=self.user,
            page=self.page,
            content="TODO: Original task",
        )
        todo_block = create_command.execute()
        self.assertEqual(todo_block.block_type, "todo")

        # Update to regular content - should keep todo type
        command = UpdateBlockCommand(
            user=self.user, block_id=todo_block.uuid, content="Just regular content now"
        )
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "todo")

    def test_should_not_auto_detect_when_content_not_updated(self):
        """Test that auto-detection only happens when content is updated"""
        # Create a bullet block
        original_block = self.block

        # Update other field, not content
        command = UpdateBlockCommand(
            user=self.user, block_id=original_block.uuid, order=5
        )
        updated_block = command.execute()

        # Block type should remain unchanged
        self.assertEqual(updated_block.block_type, "bullet")
        self.assertEqual(updated_block.order, 5)

    def test_should_handle_empty_content_update(self):
        """Test that updating to empty content preserves block type"""
        command = UpdateBlockCommand(
            user=self.user, block_id=self.block.uuid, content=""
        )
        updated_block = command.execute()

        self.assertEqual(updated_block.block_type, "bullet")
        self.assertEqual(updated_block.content, "")

    def test_should_raise_validation_error_for_nonexistent_block(self):
        """Test that updating nonexistent block raises ValidationError"""
        command = UpdateBlockCommand(
            user=self.user, block_id="nonexistent-uuid", content="New content"
        )

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
                command = UpdateBlockCommand(
                    user=self.user, block_id=self.block.uuid, content=content
                )
                updated_block = command.execute()
                self.assertEqual(updated_block.block_type, expected_type)

    @patch.object(Block, "set_tags_from_content")
    def test_should_call_set_tags_from_content_when_content_updated(
        self, mock_set_tags
    ):
        """Test that tags are extracted when content is updated"""
        command = UpdateBlockCommand(
            user=self.user,
            block_id=self.block.uuid,
            content="TODO: Buy #groceries and #food",
        )
        updated_block = command.execute()

        mock_set_tags.assert_called_once_with(
            "TODO: Buy #groceries and #food", self.user
        )

    @patch.object(Block, "set_tags_from_content")
    def test_should_not_call_set_tags_from_content_when_content_not_updated(
        self, mock_set_tags
    ):
        """Test that tag extraction is skipped when content isn't updated"""
        command = UpdateBlockCommand(user=self.user, block_id=self.block.uuid, order=10)
        updated_block = command.execute()

        mock_set_tags.assert_not_called()
