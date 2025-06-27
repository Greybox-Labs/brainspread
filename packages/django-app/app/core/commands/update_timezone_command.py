from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms import UpdateTimezoneForm
from ..models import User
from ..repositories import UserRepository


class UpdateTimezoneCommand(AbstractBaseCommand):
    def __init__(self, form: UpdateTimezoneForm, user: User) -> None:
        self.form = form
        self.user = user

    def execute(self) -> User:
        super().execute()

        timezone = self.form.cleaned_data["timezone"]

        updated_user = UserRepository.update_timezone(self.user, timezone)

        return updated_user
