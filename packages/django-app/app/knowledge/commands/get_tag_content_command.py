from typing import Any, Dict, Optional

from common.commands.abstract_base_command import AbstractBaseCommand
from core.models import User

from ..forms import GetTagContentForm
from ..repositories import PageRepository


class GetTagContentCommand(AbstractBaseCommand):
    """Command to get all content associated with a specific tag (now using page-based tags)"""

    def __init__(self, form: GetTagContentForm) -> None:
        super().__init__()
        self.form = form

    def execute(self) -> Optional[Dict[str, Any]]:
        """Execute the command"""
        user: User = self.form.cleaned_data["user"]
        tag_name: str = self.form.cleaned_data["tag_name"]

        repository = PageRepository()

        # Look for tag page
        tag_page = repository.get_tag_page(tag_name, user)

        if not tag_page:
            return None

        # Get all blocks that belong to this tag page
        blocks = tag_page.tagged_blocks.all()

        # Get all pages that have blocks with this tag (excluding the tag page itself)
        pages = []
        for block in blocks:
            if block.page != tag_page and block.page not in pages:
                pages.append(block.page)

        return {
            "tag_page": tag_page,
            "blocks": blocks,
            "pages": pages,
        }
