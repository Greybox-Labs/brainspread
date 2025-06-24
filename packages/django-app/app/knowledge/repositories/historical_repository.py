from datetime import timedelta

from django.utils import timezone

from common.repositories.base_repository import BaseRepository

from ..models import Block, Page


class HistoricalRepository(BaseRepository):
    """Repository for retrieving historical pages and blocks data"""

    def get_historical_pages(self, user, days_back=30, limit=50):
        """Get pages modified within the specified time range"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)

        return Page.objects.filter(
            user=user, modified_at__gte=start_date, modified_at__lte=end_date
        ).order_by("-date", "-modified_at")[:limit]

    def get_historical_blocks(self, user, days_back=30, limit=50):
        """Get blocks modified within the specified time range"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)

        return (
            Block.objects.filter(
                user=user, modified_at__gte=start_date, modified_at__lte=end_date
            )
            .select_related("page")
            .order_by("-modified_at")[:limit]
        )

    def get_page_recent_blocks(self, page, limit=3):
        """Get recent blocks for a specific page"""
        return page.blocks.all().order_by("-modified_at")[:limit]

    def get_historical_data(self, user, days_back=30, limit=50):
        """Get combined historical data for pages and blocks"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)

        pages = self.get_historical_pages(user, days_back, limit)
        blocks = self.get_historical_blocks(user, days_back, limit)

        return {
            "pages": pages,
            "blocks": blocks,
            "date_range": {
                "start": start_date,
                "end": end_date,
                "days_back": days_back,
            },
        }
