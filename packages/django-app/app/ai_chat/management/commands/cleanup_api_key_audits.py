"""
Django management command to clean up old API key audit logs.

This command removes audit logs older than a specified number of days
to prevent the audit table from growing indefinitely.
"""
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

from ai_chat.models import APIKeyAudit


class Command(BaseCommand):
    help = 'Clean up old API key audit logs to prevent table bloat'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Delete audit logs older than this many days (default: 365)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without making changes',
        )
        parser.add_argument(
            '--keep-failed',
            action='store_true',
            help='Keep failed operations even if they are old (for security analysis)',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        keep_failed = options['keep_failed']
        
        if days <= 0:
            self.stderr.write(
                self.style.ERROR('Days must be a positive number')
            )
            return
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Build query
        audit_query = APIKeyAudit.objects.filter(created_at__lt=cutoff_date)
        
        if keep_failed:
            audit_query = audit_query.filter(success=True)
        
        total_count = audit_query.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'No audit logs older than {days} days found.')
            )
            return
        
        self.stdout.write(
            f'Found {total_count} audit logs older than {days} days to clean up.'
        )
        
        if keep_failed:
            self.stdout.write(
                'Failed operations will be preserved for security analysis.'
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No changes will be made.')
            )
            
            # Show breakdown by operation type
            operation_counts = {}
            for audit in audit_query.values('operation').annotate(
                count=models.Count('id')
            ):
                operation_counts[audit['operation']] = audit['count']
            
            self.stdout.write('Breakdown by operation type:')
            for operation, count in operation_counts.items():
                self.stdout.write(f'  {operation}: {count}')
            
            return
        
        # Perform cleanup
        try:
            deleted_count, _ = audit_query.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} audit log entries older than {days} days.'
                )
            )
            
            # Show remaining count
            remaining_count = APIKeyAudit.objects.count()
            self.stdout.write(
                f'Remaining audit log entries: {remaining_count}'
            )
            
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error during cleanup: {str(e)}')
            )