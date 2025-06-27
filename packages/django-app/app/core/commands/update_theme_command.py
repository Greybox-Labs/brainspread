from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms import UpdateThemeForm
from ..models.user import User
from ..repositories.user_repository import UserRepository


class UpdateThemeCommand(AbstractBaseCommand):
    def __init__(self, form: UpdateThemeForm) -> None:
        self.form = form

    def execute(self) -> User:
        super().execute()

        user = self.form.cleaned_data["user"]
        theme = self.form.cleaned_data["theme"]

        updated_user = UserRepository.update_theme(user, theme)

        return updated_user
