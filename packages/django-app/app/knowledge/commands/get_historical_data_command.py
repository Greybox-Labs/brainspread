from datetime import timedelta
from typing import Any, Dict

from django.utils import timezone

from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms.get_historical_data_form import GetHistoricalDataForm
from ..repositories.block_repository import BlockRepository
from ..repositories.page_repository import PageRepository


class GetHistoricalDataCommand(AbstractBaseCommand):
    """Command to retrieve historical pages and blocks data"""

    def __init__(self, form: GetHistoricalDataForm):
        self.form = form

    def execute(self) -> Dict[str, Any]:
        """Execute the command and return historical data"""
        super().execute()

        days_back = self.form.cleaned_data.get("days_back", 30)
        limit = self.form.cleaned_data.get("limit", 50)
        user = self.form.cleaned_data.get("user")

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)

        pages = PageRepository.get_pages_by_date_range(
            user=user, start_date=start_date, end_date=end_date, limit=limit
        )

        blocks = BlockRepository.get_blocks_by_date_range(
            user=user, start_date=start_date, end_date=end_date, limit=limit
        )

        return {
            "pages": pages,
            "blocks": blocks,
            "date_range": {
                "start": start_date,
                "end": end_date,
                "days_back": days_back,
            },
        }
