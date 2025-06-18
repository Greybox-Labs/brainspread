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
                if field == "content":
                    content_updated = True

        # Auto-detect block type from content if content was updated
        if content_updated:
            auto_detected_type = self._detect_block_type_from_content(block.content, block.block_type)
            if auto_detected_type != block.block_type:
                block.block_type = auto_detected_type

        block.save()

        # Extract and set tags if content was updated (business logic)
        if content_updated and block.content:
            block.set_tags_from_content(block.content, self.user)
            # Refresh block from database to get updated tag relationships
            block.refresh_from_db()

        return block

    def _detect_block_type_from_content(self, content: str, current_block_type: str) -> str:
        """Auto-detect block type from content patterns"""
        # Only auto-detect for bullet, todo, and done types
        # Don't override other explicit types like heading, code, etc.
        if current_block_type not in ["bullet", "todo", "done"]:
            return current_block_type
            
        # Only auto-detect if we have content
        if not content:
            return current_block_type
            
        content_stripped = content.strip()
        content_lower = content_stripped.lower()
        
        # Check for TODO patterns
        if content_lower.startswith('todo'):
            return "todo"
        elif content_lower.startswith('[ ]'):
            return "todo"
        elif content_lower.startswith('[x]'):
            return "done"
        elif content_lower.startswith('☐'):
            return "todo"
        elif content_lower.startswith('☑'):
            return "done"
        
        # If none of the patterns match, keep current type
        return current_block_type
