from common.commands.abstract_base_command import AbstractBaseCommand
from ..repositories.user_repository import UserRepository
from ..models.user import User
from ..forms import UpdateThemeForm


class UpdateThemeCommand(AbstractBaseCommand):
    def __init__(self, form: UpdateThemeForm, user: User) -> None:
        self.form = form
        self.user = user

    def execute(self) -> User:
        super().execute()

        theme = self.form.cleaned_data["theme"]

        updated_user = UserRepository.update_theme(self.user, theme)

        return updated_user