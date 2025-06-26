from typing import List, Optional
from django.utils import timezone
from django.db.models import QuerySet

from common.repositories.base_repository import BaseRepository
from core.models import APIKey, APIKeyAudit


class APIKeyRepository(BaseRepository):
    model = APIKey
    
    @classmethod
    def get_user_api_keys(cls, user, active_only: bool = True) -> QuerySet[APIKey]:
        """
        Get all API keys for a user.
        
        Args:
            user: User instance
            active_only: If True, only return active keys
            
        Returns:
            QuerySet of APIKey instances
        """
        queryset = cls.model.objects.filter(user=user)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
            
        return queryset.order_by('-created_at')
    
    @classmethod
    def get_active_key_by_name(cls, user, name: str) -> Optional[APIKey]:
        """
        Get an active API key by name for a user.
        
        Args:
            user: User instance
            name: API key name
            
        Returns:
            APIKey instance or None if not found
        """
        try:
            return cls.model.objects.get(
                user=user,
                name=name,
                is_active=True
            )
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_expired_keys(cls) -> QuerySet[APIKey]:
        """
        Get all expired API keys.
        
        Returns:
            QuerySet of expired APIKey instances
        """
        now = timezone.now()
        return cls.model.objects.filter(
            expires_at__lt=now,
            is_active=True
        )
    
    @classmethod
    def deactivate_key(cls, api_key: APIKey) -> APIKey:
        """
        Deactivate an API key.
        
        Args:
            api_key: APIKey instance to deactivate
            
        Returns:
            Updated APIKey instance
        """
        api_key.is_active = False
        api_key.save(update_fields=['is_active', 'updated_at'])
        return api_key
    
    @classmethod
    def update_last_used(cls, api_key: APIKey, ip_address: str = None) -> APIKey:
        """
        Update the last used timestamp and IP for an API key.
        
        Args:
            api_key: APIKey instance
            ip_address: IP address of the request
            
        Returns:
            Updated APIKey instance
        """
        api_key.last_used = timezone.now()
        if ip_address:
            api_key.last_used_ip = ip_address
            
        api_key.save(update_fields=['last_used', 'last_used_ip', 'updated_at'])
        return api_key


class APIKeyAuditRepository(BaseRepository):
    model = APIKeyAudit
    
    @classmethod
    def get_user_audit_logs(cls, user, limit: int = 100) -> QuerySet[APIKeyAudit]:
        """
        Get audit logs for a user.
        
        Args:
            user: User instance
            limit: Maximum number of logs to return
            
        Returns:
            QuerySet of APIKeyAudit instances
        """
        return cls.model.objects.filter(user=user)[:limit]
    
    @classmethod
    def get_key_audit_logs(cls, api_key: APIKey) -> QuerySet[APIKeyAudit]:
        """
        Get audit logs for a specific API key.
        
        Args:
            api_key: APIKey instance
            
        Returns:
            QuerySet of APIKeyAudit instances
        """
        return cls.model.objects.filter(api_key=api_key)
    
    @classmethod
    def get_failed_auth_attempts(cls, user, hours: int = 24) -> QuerySet[APIKeyAudit]:
        """
        Get failed authentication attempts for a user within a time window.
        
        Args:
            user: User instance
            hours: Time window in hours
            
        Returns:
            QuerySet of failed authentication attempts
        """
        since = timezone.now() - timezone.timedelta(hours=hours)
        return cls.model.objects.filter(
            user=user,
            action='failed_auth',
            created_at__gte=since
        )
    
    @classmethod
    def cleanup_old_logs(cls, days: int = 90) -> int:
        """
        Clean up audit logs older than specified days.
        
        Args:
            days: Number of days to keep logs
            
        Returns:
            Number of deleted records
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        result = cls.model.objects.filter(created_at__lt=cutoff_date).delete()
        return result[0] if result else 0