import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from knowledge.commands import ToggleBlockTodoCommand
from knowledge.models import Page, Block


User = get_user_model()


@pytest.mark.django_db
class TestToggleBlockTodoCommand:
    """Test the ToggleBlockTodoCommand"""

    def test_toggle_bullet_to_todo(self):
        """Test toggling a bullet block to todo"""
        user = User.objects.create_user(email="test@example.com", password="password")
        page = Page.objects.create(title="Test Page", user=user)
        block = Block.objects.create(
            page=page,
            user=user,
            content="Test block",
            block_type="bullet",
            order=0
        )

        command = ToggleBlockTodoCommand(user, block.uuid)
        result = command.execute()

        assert result.block_type == "todo"
        
        # Verify in database
        block.refresh_from_db()
        assert block.block_type == "todo"

    def test_toggle_todo_to_done(self):
        """Test toggling a todo block to done"""
        user = User.objects.create_user(email="test@example.com", password="password")
        page = Page.objects.create(title="Test Page", user=user)
        block = Block.objects.create(
            page=page,
            user=user,
            content="Test todo",
            block_type="todo",
            order=0
        )

        command = ToggleBlockTodoCommand(user, block.uuid)
        result = command.execute()

        assert result.block_type == "done"
        
        # Verify in database
        block.refresh_from_db()
        assert block.block_type == "done"

    def test_toggle_done_to_bullet(self):
        """Test toggling a done block to bullet"""
        user = User.objects.create_user(email="test@example.com", password="password")
        page = Page.objects.create(title="Test Page", user=user)
        block = Block.objects.create(
            page=page,
            user=user,
            content="Test done",
            block_type="done",
            order=0
        )

        command = ToggleBlockTodoCommand(user, block.uuid)
        result = command.execute()

        assert result.block_type == "bullet"
        
        # Verify in database
        block.refresh_from_db()
        assert block.block_type == "bullet"

    def test_full_cycle_toggle(self):
        """Test the full cycle: bullet -> todo -> done -> bullet"""
        user = User.objects.create_user(email="test@example.com", password="password")
        page = Page.objects.create(title="Test Page", user=user)
        block = Block.objects.create(
            page=page,
            user=user,
            content="Test cycle",
            block_type="bullet",
            order=0
        )

        # bullet -> todo
        command = ToggleBlockTodoCommand(user, block.uuid)
        result = command.execute()
        assert result.block_type == "todo"

        # todo -> done
        command = ToggleBlockTodoCommand(user, block.uuid)
        result = command.execute()
        assert result.block_type == "done"

        # done -> bullet
        command = ToggleBlockTodoCommand(user, block.uuid)
        result = command.execute()
        assert result.block_type == "bullet"

    def test_toggle_nonexistent_block(self):
        """Test toggling a non-existent block raises ValidationError"""
        user = User.objects.create_user(email="test@example.com", password="password")
        
        with pytest.raises(ValidationError, match="Block not found"):
            command = ToggleBlockTodoCommand(user, "nonexistent-uuid")
            command.execute()

    def test_toggle_unauthorized_block(self):
        """Test toggling a block owned by another user raises ValidationError"""
        user1 = User.objects.create_user(email="test1@example.com", password="password")
        user2 = User.objects.create_user(email="test2@example.com", password="password")
        
        page = Page.objects.create(title="Test Page", user=user1)
        block = Block.objects.create(
            page=page,
            user=user1,
            content="Test block",
            block_type="todo",
            order=0
        )

        with pytest.raises(ValidationError, match="Block not found"):
            command = ToggleBlockTodoCommand(user2, block.uuid)
            command.execute()