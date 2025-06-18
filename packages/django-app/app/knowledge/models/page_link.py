from django.db import models

from common.models.uuid_mixin import UUIDModelMixin
from common.models.crud_timestamps_mixin import CRUDTimestampsMixin


class PageLink(UUIDModelMixin, CRUDTimestampsMixin):
    """
    Track links between pages for bidirectional linking
    """

    source_block = models.ForeignKey(
        "Block", on_delete=models.CASCADE, related_name="outgoing_links"
    )
    target_page = models.ForeignKey(
        "Page", on_delete=models.CASCADE, related_name="incoming_links"
    )

    class Meta:
        db_table = "page_links"
        unique_together = [("source_block", "target_page")]
        indexes = [
            models.Index(fields=["target_page"]),
        ]
