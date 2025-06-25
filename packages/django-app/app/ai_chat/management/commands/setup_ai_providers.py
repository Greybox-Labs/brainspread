from django.core.management.base import BaseCommand

from ai_chat.models import AIProvider, UserAISettings, UserProviderConfig
from core.models import User


class Command(BaseCommand):
    help = "Set up AI providers and configure default settings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-email",
            type=str,
            default="admin@email.com",
            help="Email of the user to configure AI settings for",
        )

    def handle(self, *args, **options):
        user_email = options["user_email"]

        # Create AI providers
        anthropic_provider, created = AIProvider.objects.get_or_create(
            name="Anthropic", defaults={"base_url": "https://api.anthropic.com"}
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"AIProvider 'Anthropic' {'created' if created else 'already exists'} (ID: {anthropic_provider.id})"
            )
        )

        openai_provider, created = AIProvider.objects.get_or_create(
            name="OpenAI", defaults={"base_url": "https://api.openai.com"}
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"AIProvider 'OpenAI' {'created' if created else 'already exists'} (ID: {openai_provider.id})"
            )
        )

        # Get the user
        try:
            user = User.objects.get(email=user_email)
            self.stdout.write(f"Found user: {user.email}")

            # Create or update user AI settings - set Anthropic as default
            settings, created = UserAISettings.objects.get_or_create(
                user=user,
                defaults={
                    "provider": anthropic_provider,
                    "default_model": "claude-sonnet-4-20250514",
                    "api_key": "",  # Will be moved to UserProviderConfig
                },
            )

            if not created:
                # Update existing settings to use Anthropic
                settings.provider = anthropic_provider
                settings.default_model = "claude-sonnet-4-20250514"
                settings.save()
                self.stdout.write(f"Updated existing UserAISettings for {user.email}")
            else:
                self.stdout.write(f"Created new UserAISettings for {user.email}")

            # Create UserProviderConfig for Anthropic
            anthropic_config, created = UserProviderConfig.objects.get_or_create(
                user=user,
                provider=anthropic_provider,
                defaults={
                    "api_key": "",  # User will add their key via settings
                    "is_enabled": True,
                    "enabled_models": [
                        "claude-sonnet-4-20250514",
                        "claude-3-5-sonnet-20241022",
                        "claude-3-5-haiku-20241022",
                        "claude-3-opus-20240229",
                    ],
                },
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"UserProviderConfig for Anthropic {'created' if created else 'already exists'}"
                )
            )

            # Create UserProviderConfig for OpenAI
            openai_config, created = UserProviderConfig.objects.get_or_create(
                user=user,
                provider=openai_provider,
                defaults={
                    "api_key": "",  # User will add their key via settings
                    "is_enabled": True,
                    "enabled_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                },
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"UserProviderConfig for OpenAI {'created' if created else 'already exists'}"
                )
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "Setup complete! Users can now configure API keys and models in the AI Settings."
                )
            )

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"User with email '{user_email}' not found. Please create a user first or use --user-email option."
                )
            )
