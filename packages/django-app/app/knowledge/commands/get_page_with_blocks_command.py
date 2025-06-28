from typing import List, Tuple

import pytz
from django.utils import timezone

from common.commands.abstract_base_command import AbstractBaseCommand
from knowledge.models import Block, Page
from knowledge.repositories import BlockRepository, PageRepository

from ..forms.get_page_with_blocks_form import GetPageWithBlocksForm


class GetPageWithBlocksCommand(AbstractBaseCommand):
    """Command to get a page with all its blocks"""

    def __init__(self, form: GetPageWithBlocksForm) -> None:
        self.form = form

    def execute(self) -> Tuple[Page, List[Block]]:
        """Execute the command"""
        super().execute()

        user = self.form.cleaned_data.get("user")
        page = self.form.cleaned_data.get("page")
        date = self.form.cleaned_data.get("date")

        if date:
            page, created = PageRepository.get_or_create_daily_note(user, date)
        elif not page:
            try:
                if user.timezone and user.timezone != "UTC":
                    user_tz = pytz.timezone(user.timezone)
                    now_user_tz = timezone.now().astimezone(user_tz)
                    today = now_user_tz.date()
                else:
                    today = timezone.now().date()
            except Exception:
                today = timezone.now().date()

            page, created = PageRepository.get_or_create_daily_note(user, today)

        root_blocks = BlockRepository.get_root_blocks(page)

        return page, list(root_blocks)
