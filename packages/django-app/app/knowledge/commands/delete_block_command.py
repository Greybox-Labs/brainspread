from django.core.exceptions import ValidationError

from common.commands.abstract_base_command import AbstractBaseCommand
from ..models import Block


class DeleteBlockCommand(AbstractBaseCommand):
    """Command to delete a block"""

    def __init__(self, user, block_id):
        self.user = user
        self.block_id = block_id

    def execute(self) -> bool:
        """Execute the command"""
        try:
            block = Block.objects.get(uuid=self.block_id, user=self.user)
            block.delete()
            return True
        except Block.DoesNotExist:
            raise ValidationError("Block not found")
