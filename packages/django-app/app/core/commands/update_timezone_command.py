from typing import Any, Dict

from common.commands.abstract_base_command import AbstractBaseCommand
from ..repositories.user_repository import UserRepository
from ..forms import UpdateTimezoneForm
from ..models import User


class UpdateTimezoneCommand(AbstractBaseCommand):
    def __init__(self, form: UpdateTimezoneForm, user: User) -> None:
        self.form = form
        self.user = user

    def execute(self) -> Dict[str, Any]:
        super().execute()

        timezone = self.form.cleaned_data["timezone"]

        updated_user = UserRepository.update_timezone(self.user, timezone)

        return {
            "user": {
                "id": str(updated_user.uuid),
                "email": updated_user.email,
                "timezone": updated_user.timezone,
            }
        }
