from typing import Any, Dict, Optional

from common.commands.abstract_base_command import AbstractBaseCommand
from core.models import User

from ..forms import GetTagContentForm
from ..repositories import TagRepository


class GetTagContentCommand(AbstractBaseCommand):
    """Command to get all content associated with a specific tag"""

    def __init__(self, form: GetTagContentForm) -> None:
        super().__init__()
        self.form = form

    def execute(self) -> Optional[Dict[str, Any]]:
        """Execute the command"""
        user: User = self.form.cleaned_data["user"]
        tag_name: str = self.form.cleaned_data["tag_name"]

        repository = TagRepository()
        return repository.get_tag_with_content(tag_name, user)
