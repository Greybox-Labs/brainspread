from typing import NamedTuple

from rest_framework.authtoken.models import Token

from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms import RegisterForm
from ..models.user import User
from ..repositories.user_repository import UserRepository


class RegisterResult(NamedTuple):
    user: User
    token: str


class RegisterCommand(AbstractBaseCommand):
    def __init__(self, form: RegisterForm) -> None:
        self.form = form

    def execute(self) -> RegisterResult:
        super().execute()

        email = self.form.cleaned_data["email"]
        password = self.form.cleaned_data["password"]

        user = UserRepository.create_user(email=email, password=password)
        token, created = Token.objects.get_or_create(user=user)

        return RegisterResult(user=user, token=token.key)
