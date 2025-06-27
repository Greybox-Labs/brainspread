from common.commands.abstract_base_command import AbstractBaseCommand

from ..models.user import User


class GetUserProfileCommand(AbstractBaseCommand):
    def __init__(self, user: User) -> None:
        self.user = user
        self.form = None

    def execute(self) -> User:
        super().execute()
        return self.user
