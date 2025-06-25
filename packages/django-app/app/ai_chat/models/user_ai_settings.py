from django.conf import settings
from django.db import models

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin

from .ai_provider import AIProvider


class UserAISettings(UUIDModelMixin, CRUDTimestampsMixin):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.ForeignKey(AIProvider, on_delete=models.SET_NULL, null=True)
    default_model = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "user_ai_settings"

    def __str__(self) -> str:
        return f"{self.user.email} settings"
