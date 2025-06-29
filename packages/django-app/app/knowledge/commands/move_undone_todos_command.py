from datetime import date

from common.commands.abstract_base_command import AbstractBaseCommand
from common.forms.user_form import UserForm

from ..repositories import BlockRepository
from ..repositories.page_repository import PageRepository


class MoveUndoneTodosCommand(AbstractBaseCommand):
    """Command to move past undone TODOs to current day"""

    def __init__(self, form: UserForm) -> None:
        self.form = form

    def execute(self) -> dict:
        """Execute the command"""
        super().execute()  # This validates the form

        user = self.form.cleaned_data["user"]
        today = date.today()

        # Get or create today's daily note page
        today_page, created = PageRepository.get_or_create_daily_note(user, today)

        # Find all past undone TODO blocks
        past_todos = list(BlockRepository.get_past_undone_todos(user, today))

        if not past_todos:
            return {
                "moved_count": 0,
                "target_page": today_page,
                "message": "No past undone TODOs found to move",
            }

        # Move the blocks to today's page
        success = BlockRepository.move_blocks_to_page(past_todos, today_page)

        if not success:
            raise Exception("Failed to move blocks to today's page")

        return {
            "moved_count": len(past_todos),
            "target_page": today_page,
            "moved_blocks": past_todos,
            "message": f"Moved {len(past_todos)} undone TODOs to today's page",
        }
