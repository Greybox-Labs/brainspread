from common.commands.abstract_base_command import AbstractBaseCommand
from ..models import Block


class CreateBlockCommand(AbstractBaseCommand):
    """Command to create a new block"""

    def __init__(
        self,
        user,
        page,
        content="",
        content_type="text",
        block_type="bullet",
        order=0,
        parent=None,
        media_url="",
        media_metadata=None,
        properties=None,
    ):
        self.user = user
        self.page = page
        self.content = content
        self.content_type = content_type
        self.block_type = block_type
        self.order = order
        self.parent = parent
        self.media_url = media_url
        self.media_metadata = media_metadata or {}
        self.properties = properties or {}

    def execute(self) -> Block:
        """Execute the command"""
        # Auto-detect block type from content if not explicitly set
        final_block_type = self._detect_block_type_from_content()

        # Create the block
        block = Block.objects.create(
            user=self.user,
            page=self.page,
            parent=self.parent,
            content=self.content,
            content_type=self.content_type,
            block_type=final_block_type,
            order=self.order,
            media_url=self.media_url,
            media_metadata=self.media_metadata,
            properties=self.properties,
        )

        # Extract and set tags from content (business logic)
        if block.content:
            block.set_tags_from_content(block.content, self.user)
            # Refresh block from database to get updated tag relationships
            block.refresh_from_db()

        return block

    def _detect_block_type_from_content(self) -> str:
        """Auto-detect block type from content patterns"""
        # If block_type was explicitly provided and isn't default, use it
        if self.block_type != "bullet":
            return self.block_type

        # Only auto-detect if we have content
        if not self.content:
            return self.block_type

        content_stripped = self.content.strip()
        content_lower = content_stripped.lower()

        # Check for TODO patterns
        if content_lower.startswith("todo"):
            return "todo"
        elif content_lower.startswith("[ ]"):
            return "todo"
        elif content_lower.startswith("[x]"):
            return "done"
        elif content_lower.startswith("☐"):
            return "todo"
        elif content_lower.startswith("☑"):
            return "done"

        # Default to original block_type
        return self.block_type
