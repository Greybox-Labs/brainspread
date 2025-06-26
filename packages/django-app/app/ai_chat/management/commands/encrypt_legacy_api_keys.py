"""
Django management command to encrypt existing plain-text API keys.

This command migrates legacy plain-text API keys to the new encrypted format.
It should be run once after the security update is deployed.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from ai_chat.models import UserProviderConfig


class Command(BaseCommand):
    help = 'Encrypt existing plain-text API keys to use the new secure storage format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be encrypted without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force encryption even if encrypted data already exists',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Find configurations with plain-text API keys
        configs_with_legacy_keys = UserProviderConfig.objects.filter(
            api_key__isnull=False
        ).exclude(api_key__exact='')
        
        if not force:
            # Only process configs that don't already have encrypted data
            configs_with_legacy_keys = configs_with_legacy_keys.filter(
                encrypted_api_key__exact='',
                api_key_salt__exact=''
            )
        
        total_count = configs_with_legacy_keys.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No legacy API keys found to encrypt.')
            )
            return
        
        self.stdout.write(
            f'Found {total_count} API keys to encrypt.'
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No changes will be made.')
            )
            for config in configs_with_legacy_keys:
                self.stdout.write(
                    f'Would encrypt: {config.user.email} - {config.provider.name}'
                )
            return
        
        # Process encryption
        encrypted_count = 0
        failed_count = 0
        
        with transaction.atomic():
            for config in configs_with_legacy_keys:
                try:
                    # Store the plain-text key
                    legacy_key = config.api_key
                    
                    # Encrypt the key
                    success = config.set_api_key(legacy_key, hash_only=False)
                    
                    if success:
                        config.save()
                        encrypted_count += 1
                        self.stdout.write(
                            f'Encrypted: {config.user.email} - {config.provider.name}'
                        )
                    else:
                        failed_count += 1
                        self.stderr.write(
                            f'Failed to encrypt: {config.user.email} - {config.provider.name}'
                        )
                        
                except Exception as e:
                    failed_count += 1
                    self.stderr.write(
                        f'Error encrypting {config.user.email} - {config.provider.name}: {str(e)}'
                    )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Encryption completed: {encrypted_count} successful, {failed_count} failed'
            )
        )
        
        if failed_count > 0:
            self.stderr.write(
                self.style.ERROR(
                    f'{failed_count} API keys failed to encrypt. Check the errors above.'
                )
            )