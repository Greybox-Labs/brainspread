from datetime import date

from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms.move_undone_todos_form import MoveUndoneTodosForm
from ..repositories import BlockRepository
from ..repositories.page_repository import PageRepository


class MoveUndoneTodosCommand(AbstractBaseCommand):
    """Command to move past undone TODOs to current day or specified date"""

    def __init__(self, form: MoveUndoneTodosForm) -> None:
        self.form = form

    def execute(self) -> dict:
        """Execute the command"""
        super().execute()  # This validates the form

        user = self.form.cleaned_data["user"]
        target_date = self.form.cleaned_data.get("target_date") or date.today()

        # Get or create target date's daily note page
        target_page, created = PageRepository.get_or_create_daily_note(
            user, target_date
        )

        # Find all undone TODO blocks
        past_todos = list(BlockRepository.get_undone_todos(user))

        if not past_todos:
            return {
                "moved_count": 0,
                "target_page": target_page,
                "message": "No undone TODOs found to move",
            }

        # Move the blocks to target page
        success = BlockRepository.move_blocks_to_page(past_todos, target_page)

        if not success:
            raise Exception("Failed to move blocks to target page")

        return {
            "moved_count": len(past_todos),
            "target_page": target_page,
            "moved_blocks": past_todos,
            "message": f"Moved {len(past_todos)} undone TODOs to {target_date.strftime('%Y-%m-%d')} page",
        }
