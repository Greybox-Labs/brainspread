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

        # Toggle todo status (business logic)
        if block.block_type == "todo":
            block.block_type = "done"
        elif block.block_type == "done":
            block.block_type = "bullet"
        else:
            block.block_type = "todo"

        block.save()
        return block
