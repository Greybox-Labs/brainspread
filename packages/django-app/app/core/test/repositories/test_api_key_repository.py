from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from core.repositories import APIKeyRepository, APIKeyAuditRepository
from core.models import APIKey, APIKeyAudit
from core.test.helpers import UserFactory, APIKeyFactory, APIKeyAuditFactory


class APIKeyRepositoryTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_get_user_api_keys_active_only(self):
        """Test getting only active API keys for a user."""
        active_key = APIKeyFactory(user=self.user, is_active=True)
        inactive_key = APIKeyFactory(user=self.user, is_active=False)
        other_user_key = APIKeyFactory(is_active=True)  # Different user
        
        result = APIKeyRepository.get_user_api_keys(self.user, active_only=True)
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), active_key)

    def test_get_user_api_keys_all(self):
        """Test getting all API keys for a user."""
        active_key = APIKeyFactory(user=self.user, is_active=True)
        inactive_key = APIKeyFactory(user=self.user, is_active=False)
        other_user_key = APIKeyFactory(is_active=True)  # Different user
        
        result = APIKeyRepository.get_user_api_keys(self.user, active_only=False)
        
        self.assertEqual(result.count(), 2)
        key_ids = [key.id for key in result]
        self.assertIn(active_key.id, key_ids)
        self.assertIn(inactive_key.id, key_ids)
        self.assertNotIn(other_user_key.id, key_ids)

    def test_get_active_key_by_name(self):
        """Test getting an active API key by name."""
        api_key = APIKeyFactory(user=self.user, name="test-key", is_active=True)
        inactive_key = APIKeyFactory(user=self.user, name="inactive-key", is_active=False)
        
        # Should find active key
        result = APIKeyRepository.get_active_key_by_name(self.user, "test-key")
        self.assertEqual(result, api_key)
        
        # Should not find inactive key
        result = APIKeyRepository.get_active_key_by_name(self.user, "inactive-key")
        self.assertIsNone(result)
        
        # Should not find nonexistent key
        result = APIKeyRepository.get_active_key_by_name(self.user, "nonexistent")
        self.assertIsNone(result)

    def test_get_expired_keys(self):
        """Test getting expired API keys."""
        # Create expired key
        expired_key = APIKeyFactory(
            expires_at=timezone.now() - timedelta(hours=1),
            is_active=True
        )
        
        # Create non-expired key
        active_key = APIKeyFactory(
            expires_at=timezone.now() + timedelta(hours=1),
            is_active=True
        )
        
        # Create key without expiration
        no_expiry_key = APIKeyFactory(expires_at=None, is_active=True)
        
        # Create inactive expired key
        inactive_expired_key = APIKeyFactory(
            expires_at=timezone.now() - timedelta(hours=1),
            is_active=False
        )
        
        result = APIKeyRepository.get_expired_keys()
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), expired_key)

    def test_deactivate_key(self):
        """Test deactivating an API key."""
        api_key = APIKeyFactory(is_active=True)
        
        result = APIKeyRepository.deactivate_key(api_key)
        
        self.assertEqual(result, api_key)
        self.assertFalse(result.is_active)
        
        # Check in database
        api_key.refresh_from_db()
        self.assertFalse(api_key.is_active)

    def test_update_last_used(self):
        """Test updating last used timestamp and IP."""
        api_key = APIKeyFactory()
        original_last_used = api_key.last_used
        
        result = APIKeyRepository.update_last_used(api_key, "192.168.1.1")
        
        self.assertEqual(result, api_key)
        self.assertNotEqual(result.last_used, original_last_used)
        self.assertEqual(result.last_used_ip, "192.168.1.1")
        
        # Check in database
        api_key.refresh_from_db()
        self.assertEqual(api_key.last_used_ip, "192.168.1.1")
        self.assertIsNotNone(api_key.last_used)

    def test_update_last_used_without_ip(self):
        """Test updating last used timestamp without IP."""
        api_key = APIKeyFactory()
        original_last_used = api_key.last_used
        original_ip = api_key.last_used_ip
        
        result = APIKeyRepository.update_last_used(api_key)
        
        self.assertNotEqual(result.last_used, original_last_used)
        self.assertEqual(result.last_used_ip, original_ip)  # Should not change


class APIKeyAuditRepositoryTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.api_key = APIKeyFactory(user=self.user)

    def test_get_user_audit_logs(self):
        """Test getting audit logs for a user."""
        # Create audit logs for the user
        audit1 = APIKeyAuditFactory(user=self.user, api_key=self.api_key)
        audit2 = APIKeyAuditFactory(user=self.user, api_key=self.api_key)
        
        # Create audit log for different user
        other_user = UserFactory()
        other_audit = APIKeyAuditFactory(user=other_user)
        
        result = APIKeyAuditRepository.get_user_audit_logs(self.user)
        
        self.assertEqual(result.count(), 2)
        audit_ids = [audit.id for audit in result]
        self.assertIn(audit1.id, audit_ids)
        self.assertIn(audit2.id, audit_ids)
        self.assertNotIn(other_audit.id, audit_ids)

    def test_get_user_audit_logs_with_limit(self):
        """Test getting audit logs with limit."""
        # Create multiple audit logs
        for i in range(5):
            APIKeyAuditFactory(user=self.user, api_key=self.api_key)
        
        result = APIKeyAuditRepository.get_user_audit_logs(self.user, limit=3)
        
        self.assertEqual(len(result), 3)

    def test_get_key_audit_logs(self):
        """Test getting audit logs for a specific API key."""
        # Create audit logs for the key
        audit1 = APIKeyAuditFactory(user=self.user, api_key=self.api_key)
        audit2 = APIKeyAuditFactory(user=self.user, api_key=self.api_key)
        
        # Create audit log for different key
        other_key = APIKeyFactory(user=self.user)
        other_audit = APIKeyAuditFactory(user=self.user, api_key=other_key)
        
        result = APIKeyAuditRepository.get_key_audit_logs(self.api_key)
        
        self.assertEqual(result.count(), 2)
        audit_ids = [audit.id for audit in result]
        self.assertIn(audit1.id, audit_ids)
        self.assertIn(audit2.id, audit_ids)
        self.assertNotIn(other_audit.id, audit_ids)

    def test_get_failed_auth_attempts(self):
        """Test getting failed authentication attempts."""
        # Create recent failed auth attempt
        recent_fail = APIKeyAuditFactory(
            user=self.user,
            action='failed_auth',
            success=False,
            created_at=timezone.now() - timedelta(hours=1)
        )
        
        # Create old failed auth attempt
        old_fail = APIKeyAuditFactory(
            user=self.user,
            action='failed_auth',
            success=False,
            created_at=timezone.now() - timedelta(days=2)
        )
        
        # Create recent successful attempt
        recent_success = APIKeyAuditFactory(
            user=self.user,
            action='used',
            success=True,
            created_at=timezone.now() - timedelta(minutes=30)
        )
        
        result = APIKeyAuditRepository.get_failed_auth_attempts(self.user, hours=24)
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), recent_fail)

    def test_cleanup_old_logs(self):
        """Test cleaning up old audit logs."""
        # Create old audit log
        old_audit = APIKeyAuditFactory(
            user=self.user,
            created_at=timezone.now() - timedelta(days=100)
        )
        
        # Create recent audit log
        recent_audit = APIKeyAuditFactory(
            user=self.user,
            created_at=timezone.now() - timedelta(days=1)
        )
        
        # Cleanup logs older than 90 days
        deleted_count = APIKeyAuditRepository.cleanup_old_logs(days=90)
        
        self.assertEqual(deleted_count, 1)
        
        # Check that only recent log remains
        remaining_logs = APIKeyAudit.objects.all()
        self.assertEqual(remaining_logs.count(), 1)
        self.assertEqual(remaining_logs.first(), recent_audit)

    def test_cleanup_old_logs_none_to_delete(self):
        """Test cleanup when no old logs exist."""
        # Create only recent audit logs
        recent_audit = APIKeyAuditFactory(
            user=self.user,
            created_at=timezone.now() - timedelta(days=1)
        )
        
        deleted_count = APIKeyAuditRepository.cleanup_old_logs(days=90)
        
        self.assertEqual(deleted_count, 0)
        
        # Check that log still exists
        self.assertTrue(APIKeyAudit.objects.filter(id=recent_audit.id).exists())