from rest_framework.authtoken.models import Token

from common.commands.abstract_base_command import AbstractBaseCommand
from common.forms.user_form import UserForm


class LogoutCommand(AbstractBaseCommand):
    def __init__(self, form: UserForm) -> None:
        self.form = form

    def execute(self) -> str:
        super().execute()
        user = self.form.cleaned_data["user"]
        try:
            token = Token.objects.get(user=user)
            token.delete()
            return "Successfully logged out"
        except Token.DoesNotExist:
            return "Already logged out"
