from django.core.management.base import BaseCommand
from core.models import User


class Command(BaseCommand):
    help = 'Create a test user'

    def handle(self, *args, **options):
        email = 'test@example.com'
        password = 'testpass123'
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(f'User {email} already exists')
        else:
            user = User.objects.create_user(email=email, password=password)
            self.stdout.write(f'Created user: {user.email}')