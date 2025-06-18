from abc import ABC, abstractmethod

from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm


class AbstractBaseCommand(ABC):
    """
    The Command interface declares a method for executing a command.
    """

    form: BaseForm | None

    @abstractmethod
    def execute(self) -> None:
        if self.form and not self.form.is_valid():
            raise ValidationError(self.form.errors.as_json())
