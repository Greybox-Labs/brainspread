from django.conf import settings
from django.db import models

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin


class ChatSession(UUIDModelMixin, CRUDTimestampsMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "ai_chat_sessions"
        ordering = ("-created_at",)


class ChatMessage(UUIDModelMixin, CRUDTimestampsMixin):
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20)  # 'user' or 'assistant'
    content = models.TextField()
    ai_model = models.ForeignKey(
        "ai_chat.AIModel", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "ai_chat_messages"
        ordering = ("created_at",)
