from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.utils import timezone

from core.commands import CreateAPIKeyCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an API key for a user'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address of the user',
        )
        parser.add_argument(
            'name',
            type=str,
            help='Name for the API key',
        )
        parser.add_argument(
            '--scope',
            type=str,
            default='read',
            choices=['read', 'write', 'read_write', 'admin'],
            help='API key scope (default: read)',
        )
        parser.add_argument(
            '--expires-days',
            type=int,
            help='Number of days until expiration (optional)',
        )
        parser.add_argument(
            '--hash-only',
            action='store_true',
            help='Store as hash only (for verification-only keys)',
        )
    
    def handle(self, *args, **options):
        email = options['email']
        name = options['name']
        scope = options['scope']
        expires_days = options.get('expires_days')
        hash_only = options['hash_only']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email "{email}" does not exist')
        
        expires_at = None
        if expires_days:
            expires_at = timezone.now() + timedelta(days=expires_days)
        
        try:
            command = CreateAPIKeyCommand(
                user=user,
                name=name,
                scope=scope,
                expires_at=expires_at,
                store_encrypted=not hash_only,
                ip_address='127.0.0.1',  # Management command
                user_agent='Management Command',
            )
            
            result = command.execute()
            
            self.stdout.write(self.style.SUCCESS('API key created successfully!'))
            self.stdout.write(f'User: {user.email}')
            self.stdout.write(f'Name: {result["api_key"]["name"]}')
            self.stdout.write(f'UUID: {result["api_key"]["uuid"]}')
            self.stdout.write(f'Scope: {result["api_key"]["scope"]}')
            self.stdout.write(f'Storage Type: {result["storage_type"]}')
            
            if expires_at:
                self.stdout.write(f'Expires: {expires_at.isoformat()}')
            
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('IMPORTANT: Save this API key value - it will not be shown again!'))
            self.stdout.write(f'API Key: {result["key_value"]}')
            
        except Exception as e:
            raise CommandError(f'Failed to create API key: {str(e)}')