from django.db import models

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin


class AIProvider(UUIDModelMixin, CRUDTimestampsMixin):
    """Stores configuration for an AI provider"""

    name = models.CharField(max_length=50)
    base_url = models.URLField(blank=True, null=True)
    # Store API key per user via UserAISettings

    class Meta:
        db_table = "ai_providers"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name
