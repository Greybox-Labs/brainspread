from typing import Optional

from django import forms
from django.core.exceptions import ValidationError

from common.forms import UUIDModelChoiceField
from common.forms.base_form import BaseForm
from core.models import User
from core.repositories import UserRepository

from ..models import Block, Page
from ..repositories import BlockRepository, PageRepository


class CreateBlockForm(BaseForm):
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    page = UUIDModelChoiceField(queryset=PageRepository.get_queryset())
    content = forms.CharField(required=False, initial="")
    content_type = forms.CharField(max_length=50, required=False, initial="text")
    block_type = forms.CharField(max_length=50, required=False, initial="bullet")
    order = forms.IntegerField(min_value=0, required=False, initial=0)
    parent = UUIDModelChoiceField(
        queryset=BlockRepository.get_queryset(), required=False
    )
    media_url = forms.URLField(required=False, initial="")
    media_metadata = forms.JSONField(required=False, initial=dict)
    properties = forms.JSONField(required=False, initial=dict)

    def clean_page(self) -> Optional[Page]:
        page = self.cleaned_data.get("page")
        user = self.cleaned_data.get("user")

        if page and user and page.user != user:
            raise ValidationError("Page does not belong to the specified user")

        return page

    def clean_parent(self) -> Optional[Block]:
        user = self.cleaned_data.get("user")
        parent = None
        if "parent" in self.cleaned_data:
            parent = self.cleaned_data.get("parent")

        if parent and user and parent.user != user:
            raise ValidationError("Parent block does not belong to the specified user")

        return parent

    def clean_user(self) -> User:
        user = self.cleaned_data.get("user")
        if not user:
            raise ValidationError("User is required")
        return user
