from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm
from common.forms.uuid_model_choice_field import UUIDModelChoiceField
from core.models import User
from core.repositories import UserRepository
from knowledge.repositories import PageRepository


class GetPageWithBlocksForm(BaseForm):
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    page = UUIDModelChoiceField(queryset=PageRepository.get_queryset(), required=False)
    date = forms.DateField(required=False)

    def clean_user(self) -> User:
        user = self.cleaned_data.get("user")
        if not user:
            raise ValidationError("User is required")
        return user

    def clean_page(self):
        page = self.cleaned_data.get("page")
        user = self.cleaned_data.get("user")
        if page and user and page.user != user:
            raise ValidationError("Page not found")
        return page

    def clean(self):
        cleaned_data = super().clean()
        page = cleaned_data.get("page")
        date = cleaned_data.get("date")

        if not page and not date:
            cleaned_data["date"] = datetime.now().date()

        return cleaned_data
