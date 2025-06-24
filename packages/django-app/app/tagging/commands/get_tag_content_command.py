from common.commands.abstract_base_command import AbstractBaseCommand

from ..repositories import TagRepository


class GetTagContentCommand(AbstractBaseCommand):
    """Command to get all content associated with a specific tag"""

    def __init__(self, user, tag_name):
        super().__init__()
        self.form = None  # No form validation needed for this command
        self.user = user
        self.tag_name = tag_name

    def execute(self):
        """Execute the command"""
        repository = TagRepository()
        return repository.get_tag_with_content(self.tag_name, self.user)
