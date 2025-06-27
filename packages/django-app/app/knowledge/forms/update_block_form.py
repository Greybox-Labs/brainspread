from django import forms
from django.core.exceptions import ValidationError

from common.forms import BaseForm, UUIDModelChoiceField
from core.models import User
from core.repositories import UserRepository

from ..models import Block
from ..repositories import BlockRepository


class UpdateBlockForm(BaseForm):
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    block = UUIDModelChoiceField(queryset=BlockRepository.get_queryset(), required=True)
    content = forms.CharField(required=False)
    content_type = forms.CharField(max_length=50, required=False)
    block_type = forms.CharField(max_length=50, required=False)
    order = forms.IntegerField(min_value=0, required=False)
    parent = UUIDModelChoiceField(
        queryset=BlockRepository.get_queryset(), required=False
    )
    media_url = forms.URLField(required=False)
    media_metadata = forms.JSONField(required=False)
    properties = forms.JSONField(required=False)

    def clean_block(self) -> Block:
        block = self.cleaned_data.get("block")
        user = self.cleaned_data.get("user")

        if block and user and block.user != user:
            raise ValidationError("Block not found")

        return block

    def clean_parent(self) -> Block:
        user = self.cleaned_data.get("user")
        parent = None
        if "parent" in self.cleaned_data:
            parent = self.cleaned_data.get("parent")

        if parent and user and parent.user != user:
            raise ValidationError("Parent block not found")

        return parent

    def clean_user(self) -> User:
        user = self.cleaned_data.get("user")
        if not user:
            raise ValidationError("User is required")
        return user
