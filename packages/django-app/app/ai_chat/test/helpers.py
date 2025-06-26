import factory
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from ai_chat.models import (
    AIModel,
    AIProvider,
    ChatMessage,
    ChatSession,
    UserAISettings,
    UserProviderConfig,
)
from core.test.helpers import UserFactory


class AIProviderFactory(DjangoModelFactory):
    name = Faker("word")
    base_url = Faker("url")

    class Meta:
        model = AIProvider


class AIModelFactory(DjangoModelFactory):
    name = Faker("word")
    provider = SubFactory(AIProviderFactory)
    display_name = Faker("sentence", nb_words=2)
    description = Faker("text", max_nb_chars=100)
    is_active = True

    class Meta:
        model = AIModel


class UserAISettingsFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    preferred_model = SubFactory(AIModelFactory)

    class Meta:
        model = UserAISettings


class UserProviderConfigFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    provider = SubFactory(AIProviderFactory)
    api_key = Faker("password", length=32)
    is_enabled = True

    class Meta:
        model = UserProviderConfig
        skip_postgeneration_save = True
    
    @factory.post_generation
    def enabled_models(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            # If models are passed in, use them
            for model in extracted:
                self.enabled_models.add(model)
        else:
            # Get or create some default models for this provider
            model1, _ = AIModel.objects.get_or_create(
                name="gpt-4",
                provider=self.provider,
                defaults={
                    "display_name": "GPT-4",
                    "description": "Test GPT-4 model",
                    "is_active": True,
                }
            )
            model2, _ = AIModel.objects.get_or_create(
                name="gpt-3.5-turbo",
                provider=self.provider,
                defaults={
                    "display_name": "GPT-3.5 Turbo", 
                    "description": "Test GPT-3.5 model",
                    "is_active": True,
                }
            )
            self.enabled_models.add(model1, model2)


class ChatSessionFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    title = Faker("sentence", nb_words=3)

    class Meta:
        model = ChatSession


class ChatMessageFactory(DjangoModelFactory):
    session = SubFactory(ChatSessionFactory)
    role = "user"
    content = Faker("text", max_nb_chars=200)

    class Meta:
        model = ChatMessage
        skip_postgeneration_save = True

    @factory.post_generation
    def user_session_match(obj, create, extracted, **kwargs):
        """Ensure the message user matches the session user"""
        if create and obj.session:
            # This is handled by the model's save method, but we'll be explicit
            pass


# Factory for creating OpenAI provider
class OpenAIProviderFactory(AIProviderFactory):
    name = "OpenAI"
    base_url = "https://api.openai.com/v1"


# Factory for creating Anthropic provider
class AnthropicProviderFactory(AIProviderFactory):
    name = "Anthropic"
    base_url = "https://api.anthropic.com"
