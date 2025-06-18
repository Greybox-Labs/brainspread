from django.db import models

from common.models.uuid_mixin import UUIDModelMixin
from common.models.crud_timestamps_mixin import CRUDTimestampsMixin


class BlockReference(UUIDModelMixin, CRUDTimestampsMixin):
    """
    Track references between blocks ((block-id))
    """

    source_block = models.ForeignKey(
        "Block", on_delete=models.CASCADE, related_name="outgoing_references"
    )
    target_block = models.ForeignKey(
        "Block", on_delete=models.CASCADE, related_name="incoming_references"
    )

    class Meta:
        db_table = "block_references"
        unique_together = [("source_block", "target_block")]
        indexes = [
            models.Index(fields=["target_block"]),
        ]
