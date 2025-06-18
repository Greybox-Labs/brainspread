from rest_framework.authtoken.models import Token
from common.commands.abstract_base_command import AbstractBaseCommand


class LogoutCommand(AbstractBaseCommand):
    def __init__(self, user):
        self.user = user
        self.form = None

    def execute(self):
        try:
            token = Token.objects.get(user=self.user)
            token.delete()
            return {"message": "Successfully logged out"}
        except Token.DoesNotExist:
            return {"message": "Already logged out"}
