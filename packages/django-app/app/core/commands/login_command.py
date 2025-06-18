from rest_framework.authtoken.models import Token
from common.commands.abstract_base_command import AbstractBaseCommand


class LoginCommand(AbstractBaseCommand):
    def __init__(self, form):
        self.form = form

    def execute(self):
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
            },
        }
