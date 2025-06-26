from django import forms
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm
from core.models import User
from core.repositories import UserRepository


class GetUserPagesForm(BaseForm):
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    published_only = forms.BooleanField(required=False, initial=True)
    limit = forms.IntegerField(min_value=1, max_value=100, required=False, initial=10)
    offset = forms.IntegerField(min_value=0, required=False, initial=0)

    def clean_user(self) -> User:
        user = self.cleaned_data.get("user")
        if not user:
            raise ValidationError("User is required")
        return user
