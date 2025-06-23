from common.commands.abstract_base_command import AbstractBaseCommand
from ..repositories.user_repository import UserRepository


class UpdateThemeCommand(AbstractBaseCommand):
    def __init__(self, form, user):
        self.form = form
        self.user = user

    def execute(self):
        super().execute()

        theme = self.form.cleaned_data["theme"]

        updated_user = UserRepository.update_theme(self.user, theme)

        return {
            "user": {
                "id": str(updated_user.uuid),
                "email": updated_user.email,
                "timezone": updated_user.timezone,
                "theme": updated_user.theme,
            }
        }