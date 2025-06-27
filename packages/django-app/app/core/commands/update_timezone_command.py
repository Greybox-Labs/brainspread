from common.commands.abstract_base_command import AbstractBaseCommand

from ..forms import UpdateTimezoneForm
from ..models import User
from ..repositories import UserRepository


class UpdateTimezoneCommand(AbstractBaseCommand):
    def __init__(self, form: UpdateTimezoneForm) -> None:
        self.form = form

    def execute(self) -> User:
        super().execute()

        user = self.form.cleaned_data["user"]
        timezone = self.form.cleaned_data["timezone"]

        updated_user = UserRepository.update_timezone(user, timezone)

        return updated_user
