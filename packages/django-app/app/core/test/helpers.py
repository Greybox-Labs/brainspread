from django.contrib.auth import get_user_model
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta

from core.models import APIKey, APIKeyAudit

User = get_user_model()


class UserFactory(DjangoModelFactory):
    email = Faker("email")
    is_active = True

    class Meta:
        model = User


class APIKeyFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    name = Faker("word")
    scope = "read"
    is_active = True

    class Meta:
        model = APIKey

    @classmethod
    def create_with_encrypted_key(cls, key_value: str = None, **kwargs):
        """Create an API key with encrypted storage."""
        api_key = cls.create(**kwargs)
        if key_value is None:
            key_value = APIKey.generate_api_key()
        api_key.encrypt_key(key_value)
        api_key.save()
        return api_key, key_value

    @classmethod
    def create_with_hashed_key(cls, key_value: str = None, **kwargs):
        """Create an API key with hashed storage."""
        api_key = cls.create(**kwargs)
        if key_value is None:
            key_value = APIKey.generate_api_key()
        api_key.hash_key(key_value)
        api_key.save()
        return api_key, key_value

    @classmethod
    def create_expired(cls, **kwargs):
        """Create an expired API key."""
        kwargs['expires_at'] = timezone.now() - timedelta(days=1)
        return cls.create(**kwargs)


class APIKeyAuditFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    api_key = SubFactory(APIKeyFactory)
    api_key_name = Faker("word")
    action = "created"
    success = True

    class Meta:
        model = APIKeyAudit
