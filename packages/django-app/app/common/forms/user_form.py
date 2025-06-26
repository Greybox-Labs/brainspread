from django import forms

from common.forms.base_form import BaseForm
from core.models import User
from core.repositories import UserRepository


class UserForm(BaseForm):
    """Reusable form for commands that only need a user"""

    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())

    def clean_user(self) -> User:
        user = self.cleaned_data.get("user")
        if not user:
            raise forms.ValidationError("User is required")
        return user
