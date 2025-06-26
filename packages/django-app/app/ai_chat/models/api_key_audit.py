"""API Key audit logging models."""
from django.conf import settings
from django.db import models

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin

from .ai_provider import AIProvider


class APIKeyAudit(UUIDModelMixin, CRUDTimestampsMixin):
    """Audit log for API key operations."""
    
    class OperationType(models.TextChoices):
        CREATED = 'created', 'Created'
        UPDATED = 'updated', 'Updated'
        DELETED = 'deleted', 'Deleted'
        ACCESSED = 'accessed', 'Accessed'
        FAILED_ACCESS = 'failed_access', 'Failed Access'
        ENCRYPTED = 'encrypted', 'Encrypted'
        DECRYPTED = 'decrypted', 'Decrypted'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE)
    operation = models.CharField(max_length=20, choices=OperationType.choices)
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional metadata stored as JSON
    metadata = models.JSONField(default=dict, blank=True)
    
    # Result of the operation
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "api_key_audits"
        indexes = [
            models.Index(fields=['user', 'provider']),
            models.Index(fields=['operation']),
            models.Index(fields=['created_at']),
            models.Index(fields=['success']),
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user.email} - {self.provider.name} - {self.operation} - {self.created_at}"