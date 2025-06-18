from django.core.exceptions import ValidationError

from common.commands.abstract_base_command import AbstractBaseCommand
from ..models import Block


class UpdateBlockCommand(AbstractBaseCommand):
    """Command to update an existing block"""
    
    def __init__(self, user, block_id, **updates):
        self.user = user
        self.block_id = block_id
        self.updates = updates
    
    def execute(self) -> Block:
        """Execute the command"""
        try:
            block = Block.objects.get(uuid=self.block_id, user=self.user)
        except Block.DoesNotExist:
            raise ValidationError("Block not found")
        
        # Update fields
        content_updated = False
        for field, value in self.updates.items():
            if hasattr(block, field):
                setattr(block, field, value)
                if field == 'content':
                    content_updated = True
        
        block.save()
        
        # Extract and set tags if content was updated (business logic)
        if content_updated and block.content:
            block.set_tags_from_content(block.content, self.user)
            # Refresh block from database to get updated tag relationships
            block.refresh_from_db()
        
        return block