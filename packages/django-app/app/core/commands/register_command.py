from rest_framework.authtoken.models import Token
from common.commands.abstract_base_command import AbstractBaseCommand
from ..repositories.user_repository import UserRepository


class RegisterCommand(AbstractBaseCommand):
    def __init__(self, form):
        self.form = form

    def execute(self):
        super().execute()

        email = self.form.cleaned_data["email"]
        password = self.form.cleaned_data["password"]

        user = UserRepository.create_user(email=email, password=password)
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
