from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.uuid_mixin import UUIDModelMixin


class APIKeyAudit(
    UUIDModelMixin,
    CRUDTimestampsMixin,
):
    """
    Audit log for all API key operations.
    
    Tracks creation, usage, rotation, and deletion of API keys
    for security monitoring and compliance.
    """
    
    ACTION_CHOICES = [
        ('created', _('Created')),
        ('used', _('Used')),
        ('rotated', _('Rotated')),
        ('deactivated', _('Deactivated')),
        ('deleted', _('Deleted')),
        ('failed_auth', _('Failed Authentication')),
        ('expired', _('Expired')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='api_key_audits',
        help_text=_('User associated with the API key operation'),
    )
    
    api_key = models.ForeignKey(
        'core.APIKey',
        on_delete=models.CASCADE,
        related_name='audit_logs',
        null=True,
        blank=True,
        help_text=_('API key involved in the operation (null if deleted)'),
    )
    
    api_key_name = models.CharField(
        _('API key name'),
        max_length=100,
        help_text=_('Name of the API key at time of operation'),
    )
    
    action = models.CharField(
        _('action'),
        max_length=20,
        choices=ACTION_CHOICES,
        help_text=_('Type of operation performed on the API key'),
    )
    
    ip_address = models.GenericIPAddressField(
        _('IP address'),
        null=True,
        blank=True,
        help_text=_('IP address from which the operation was performed'),
    )
    
    user_agent = models.TextField(
        _('user agent'),
        blank=True,
        null=True,
        help_text=_('User agent string from the request'),
    )
    
    details = models.JSONField(
        _('details'),
        default=dict,
        blank=True,
        help_text=_('Additional details about the operation'),
    )
    
    success = models.BooleanField(
        _('success'),
        default=True,
        help_text=_('Whether the operation was successful'),
    )
    
    error_message = models.TextField(
        _('error message'),
        blank=True,
        null=True,
        help_text=_('Error message if operation failed'),
    )
    
    @classmethod
    def log_operation(
        cls,
        user,
        api_key,
        action: str,
        ip_address: str = None,
        user_agent: str = None,
        details: dict = None,
        success: bool = True,
        error_message: str = None,
    ):
        """
        Log an API key operation.
        
        Args:
            user: User who performed the operation
            api_key: APIKey instance (can be None for failed operations)
            action: Type of operation (must be in ACTION_CHOICES)
            ip_address: IP address of the request
            user_agent: User agent string
            details: Additional operation details
            success: Whether the operation succeeded
            error_message: Error message if operation failed
        """
        api_key_name = api_key.name if api_key else 'Unknown'
        
        return cls.objects.create(
            user=user,
            api_key=api_key,
            api_key_name=api_key_name,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            success=success,
            error_message=error_message,
        )
    
    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{self.user.email} - {self.action} - {self.api_key_name} - {status}"
    
    class Meta:
        db_table = "api_key_audits"
        default_permissions = ()
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['api_key', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['success', 'created_at']),
        ]