import re
from django.core.exceptions import ValidationError

from common.commands.abstract_base_command import AbstractBaseCommand
from ..models import Block


class ToggleBlockTodoCommand(AbstractBaseCommand):
    """Command to toggle a block's todo status"""

    def __init__(self, user, block_id):
        self.user = user
        self.block_id = block_id

    def execute(self) -> Block:
        """Execute the command"""
        try:
            block = Block.objects.get(uuid=self.block_id, user=self.user)
        except Block.DoesNotExist:
            raise ValidationError("Block not found")

        # Toggle todo status and update content (business logic)
        if block.block_type == "todo":
            block.block_type = "done"
            block.content = self._replace_todo_with_done(block.content)
        elif block.block_type == "done":
            block.block_type = "todo"
            block.content = self._replace_done_with_todo(block.content)
        else:
            block.block_type = "todo"
            # For non-todo blocks, prepend TODO if content doesn't start with it
            if not re.match(r'^\s*todo\b', block.content, re.IGNORECASE):
                block.content = f"TODO {block.content}".strip()

        block.save()
        return block

    def _replace_todo_with_done(self, content: str) -> str:
        """Replace TODO with DONE in content, preserving case and formatting"""
        # Replace TODO: with DONE:
        content = re.sub(r'\bTODO\b(?=\s*:)', 'DONE', content)
        # Replace TODO (without colon) with DONE
        content = re.sub(r'\bTODO\b(?!\s*:)', 'DONE', content)
        # Handle lowercase variants
        content = re.sub(r'\btodo\b(?=\s*:)', 'DONE', content, flags=re.IGNORECASE)
        content = re.sub(r'\btodo\b(?!\s*:)', 'DONE', content, flags=re.IGNORECASE)
        return content

    def _replace_done_with_todo(self, content: str) -> str:
        """Replace DONE with TODO in content, preserving case and formatting"""
        # Replace DONE: with TODO:
        content = re.sub(r'\bDONE\b(?=\s*:)', 'TODO', content)
        # Replace DONE (without colon) with TODO
        content = re.sub(r'\bDONE\b(?!\s*:)', 'TODO', content)
        # Handle lowercase variants
        content = re.sub(r'\bdone\b(?=\s*:)', 'TODO', content, flags=re.IGNORECASE)
        content = re.sub(r'\bdone\b(?!\s*:)', 'TODO', content, flags=re.IGNORECASE)
        return content
