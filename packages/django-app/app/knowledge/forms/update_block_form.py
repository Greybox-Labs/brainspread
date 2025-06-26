from typing import Optional

from django import forms
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm
from core.models import User
from core.repositories import UserRepository

from ..models import Block


class UpdateBlockForm(BaseForm):
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    block_id = forms.CharField(required=True)
    content = forms.CharField(required=False)
    content_type = forms.CharField(max_length=50, required=False)
    block_type = forms.CharField(max_length=50, required=False)
    order = forms.IntegerField(min_value=0, required=False)
    parent_id = forms.CharField(required=False)
    media_url = forms.URLField(required=False)
    media_metadata = forms.JSONField(required=False)
    properties = forms.JSONField(required=False)

    def clean_block_id(self) -> str:
        block_id = self.cleaned_data.get("block_id")
        user = self.cleaned_data.get("user")

        if block_id and user:
            try:
                Block.objects.get(uuid=block_id, user=user)
            except Block.DoesNotExist:
                raise ValidationError("Block not found")

        return block_id

    def clean_parent_id(self) -> Optional[str]:
        parent_id = self.cleaned_data.get("parent_id")
        user = self.cleaned_data.get("user")

        if parent_id and user:
            try:
                Block.objects.get(uuid=parent_id, user=user)
            except Block.DoesNotExist:
                raise ValidationError("Parent block not found")

        return parent_id

    def clean_user(self) -> User:
        user = self.cleaned_data.get("user")
        if not user:
            raise ValidationError("User is required")
        return user
