from django.core.management.base import BaseCommand
from django.utils import timezone

from core.repositories import APIKeyRepository, APIKeyAuditRepository


class Command(BaseCommand):
    help = 'Cleanup expired API keys and old audit logs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep audit logs (default: 90)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        audit_days = options['days']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting API key cleanup (dry_run={dry_run})...')
        )
        
        # Cleanup expired keys
        expired_keys = APIKeyRepository.get_expired_keys()
        expired_count = expired_keys.count()
        
        if expired_count > 0:
            self.stdout.write(f'Found {expired_count} expired API keys')
            
            if not dry_run:
                for api_key in expired_keys:
                    # Deactivate the key
                    APIKeyRepository.deactivate_key(api_key)
                    
                    # Log the expiration
                    APIKeyAuditRepository.model.log_operation(
                        user=api_key.user,
                        api_key=api_key,
                        action='expired',
                        details={'cleanup_run': True}
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Deactivated {expired_count} expired API keys')
                )
            else:
                for api_key in expired_keys:
                    self.stdout.write(
                        f'Would deactivate: {api_key.user.email} - {api_key.name} '
                        f'(expired: {api_key.expires_at})'
                    )
        else:
            self.stdout.write('No expired API keys found')
        
        # Cleanup old audit logs
        if not dry_run:
            deleted_logs = APIKeyAuditRepository.cleanup_old_logs(audit_days)
            if deleted_logs > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Deleted {deleted_logs} audit logs older than {audit_days} days'
                    )
                )
            else:
                self.stdout.write(f'No audit logs older than {audit_days} days found')
        else:
            cutoff_date = timezone.now() - timezone.timedelta(days=audit_days)
            old_logs_count = APIKeyAuditRepository.model.objects.filter(
                created_at__lt=cutoff_date
            ).count()
            
            if old_logs_count > 0:
                self.stdout.write(
                    f'Would delete {old_logs_count} audit logs older than {audit_days} days'
                )
            else:
                self.stdout.write(f'No audit logs older than {audit_days} days found')
        
        self.stdout.write(self.style.SUCCESS('API key cleanup completed!'))