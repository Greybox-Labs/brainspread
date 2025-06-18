from common.commands.abstract_base_command import AbstractBaseCommand


class GetUserProfileCommand(AbstractBaseCommand):
    def __init__(self, user):
        self.user = user
        self.form = None

    def execute(self):
        return {
            "user": {
                "id": str(self.user.uuid),
                "email": self.user.email,
                "timezone": self.user.timezone,
            }
        }
