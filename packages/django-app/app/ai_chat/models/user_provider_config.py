from django.conf import settings
from django.db import models

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin
from .ai_provider import AIProvider


class UserProviderConfig(UUIDModelMixin, CRUDTimestampsMixin):
    """Stores user configuration for each AI provider"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=255, blank=True)
    is_enabled = models.BooleanField(default=True)
    enabled_models = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "user_provider_configs"
        unique_together = [("user", "provider")]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.provider.name}"