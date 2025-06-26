import factory
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from ai_chat.models import (
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


class UserAISettingsFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    provider = SubFactory(AIProviderFactory)
    default_model = Faker("word")

    class Meta:
        model = UserAISettings


class UserProviderConfigFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    provider = SubFactory(AIProviderFactory)
    api_key = Faker("password", length=32)
    is_enabled = True
    enabled_models = factory.LazyFunction(lambda: ["gpt-4", "gpt-3.5-turbo"])

    class Meta:
        model = UserProviderConfig


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
