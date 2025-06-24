from typing import Any, Dict

from rest_framework.authtoken.models import Token

from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms import LoginForm


class LoginCommand(AbstractBaseCommand):
    def __init__(self, form: LoginForm) -> None:
        self.form = form

    def execute(self) -> Dict[str, Any]:
        super().execute()

        user = self.form.cleaned_data["user"]
        timezone = self.form.cleaned_data.get("timezone")

        if timezone:
            user.timezone = timezone
            user.save(update_fields=["timezone"])

        token, created = Token.objects.get_or_create(user=user)

        return {
            "token": token.key,
            "user": {
                "id": str(user.uuid),
                "email": user.email,
                "timezone": user.timezone,
                "theme": user.theme,
            },
        }
