from django.contrib.auth import get_user_model
from factory import Faker
from factory.django import DjangoModelFactory

User = get_user_model()


class UserFactory(DjangoModelFactory):
    email = Faker("email")
    is_active = True

    class Meta:
        model = User
