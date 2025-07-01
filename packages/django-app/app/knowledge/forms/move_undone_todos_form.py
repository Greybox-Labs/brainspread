from typing import Optional

from django import forms
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm
from core.models import User
from core.repositories import UserRepository


class MoveUndoneTodosForm(BaseForm):
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    target_date = forms.DateField(required=False)

    def clean_user(self) -> User:
        user = self.cleaned_data.get("user")
        if not user:
            raise ValidationError("User is required")
        return user

    def clean_target_date(self) -> Optional[object]:
        return self.cleaned_data.get("target_date")
