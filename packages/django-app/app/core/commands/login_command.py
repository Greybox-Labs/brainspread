from typing import NamedTuple

from rest_framework.authtoken.models import Token

from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms import LoginForm
from ..models.user import User


class LoginResult(NamedTuple):
    user: User
    token: str


class LoginCommand(AbstractBaseCommand):
    def __init__(self, form: LoginForm) -> None:
        self.form = form

    def execute(self) -> LoginResult:
        super().execute()

        user = self.form.cleaned_data["user"]
        timezone = self.form.cleaned_data.get("timezone")

        if timezone:
            user.timezone = timezone
            user.save(update_fields=["timezone"])

        token, created = Token.objects.get_or_create(user=user)

        return LoginResult(user=user, token=token.key)
