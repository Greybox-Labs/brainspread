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
        # Create the block
        block = Block.objects.create(
            user=self.user,
            page=self.page,
            parent=self.parent,
            content=self.content,
            content_type=self.content_type,
            block_type=self.block_type,
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
