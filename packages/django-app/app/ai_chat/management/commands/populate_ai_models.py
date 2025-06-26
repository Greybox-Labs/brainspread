from django.core.management.base import BaseCommand

from ai_chat.models import AIModel, AIProvider


class Command(BaseCommand):
    help = "Populate AIModel table with available models from each provider"

    def handle(self, *args, **options):
        """Create AIModel entries for all available models"""

        # Model definitions
        models_data = [
            # OpenAI models
            ("OpenAI", "gpt-4", "GPT-4", "Most capable GPT-4 model"),
            (
                "OpenAI",
                "gpt-4-turbo",
                "GPT-4 Turbo",
                "Faster and more affordable GPT-4",
            ),
            ("OpenAI", "gpt-3.5-turbo", "GPT-3.5 Turbo", "Fast and affordable model"),
            (
                "OpenAI",
                "o1-preview",
                "o1-preview",
                "Reasoning model for complex problems",
            ),
            ("OpenAI", "o1-mini", "o1-mini", "Faster reasoning model"),
            # Anthropic models
            (
                "Anthropic",
                "claude-3-5-sonnet-20241022",
                "Claude 3.5 Sonnet",
                "Most intelligent Claude model",
            ),
            (
                "Anthropic",
                "claude-3-5-haiku-20241022",
                "Claude 3.5 Haiku",
                "Fast and lightweight Claude model",
            ),
            (
                "Anthropic",
                "claude-3-opus-20240229",
                "Claude 3 Opus",
                "Most capable Claude 3 model",
            ),
            (
                "Anthropic",
                "claude-3-sonnet-20240229",
                "Claude 3 Sonnet",
                "Balanced Claude 3 model",
            ),
            (
                "Anthropic",
                "claude-3-haiku-20240307",
                "Claude 3 Haiku",
                "Fast Claude 3 model",
            ),
            # Google models
            (
                "Google",
                "gemini-2.5-pro",
                "Gemini 2.5 Pro",
                "Latest and most capable Gemini model",
            ),
            (
                "Google",
                "gemini-2.5-flash",
                "Gemini 2.5 Flash",
                "Fast version of Gemini 2.5",
            ),
            (
                "Google",
                "gemini-2.0-pro",
                "Gemini 2.0 Pro",
                "Previous generation Gemini Pro",
            ),
            (
                "Google",
                "gemini-2.0-flash",
                "Gemini 2.0 Flash",
                "Previous generation Gemini Flash",
            ),
            ("Google", "gemini-1.5-pro", "Gemini 1.5 Pro", "High-quality Gemini model"),
            ("Google", "gemini-1.5-flash", "Gemini 1.5 Flash", "Fast Gemini model"),
            (
                "Google",
                "gemini-1.5-flash-8b",
                "Gemini 1.5 Flash 8B",
                "Lightweight Gemini model",
            ),
        ]

        created_count = 0
        updated_count = 0

        for provider_name, model_name, display_name, description in models_data:
            try:
                provider = AIProvider.objects.get(name__iexact=provider_name)
            except AIProvider.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"Provider '{provider_name}' not found, skipping {model_name}"
                    )
                )
                continue

            ai_model, created = AIModel.objects.get_or_create(
                name=model_name,
                defaults={
                    "provider": provider,
                    "display_name": display_name,
                    "description": description,
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(f"Created model: {model_name}")
            else:
                # Update existing model if needed
                if (
                    ai_model.display_name != display_name
                    or ai_model.description != description
                    or ai_model.provider != provider
                ):
                    ai_model.display_name = display_name
                    ai_model.description = description
                    ai_model.provider = provider
                    ai_model.save()
                    updated_count += 1
                    self.stdout.write(f"Updated model: {model_name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed models. Created: {created_count}, Updated: {updated_count}"
            )
        )
