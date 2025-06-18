import factory
from factory.django import DjangoModelFactory
from factory import Faker
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(DjangoModelFactory):
    email = Faker('email')
    is_active = True

    class Meta:
        model = User