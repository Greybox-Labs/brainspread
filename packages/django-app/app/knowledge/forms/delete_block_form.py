from django import forms
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm
from core.models import User
from core.repositories import UserRepository

from ..models import Block


class DeleteBlockForm(BaseForm):
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    block_id = forms.CharField(required=True)

    def clean_block_id(self) -> str:
        block_id = self.cleaned_data.get("block_id")
        user = self.cleaned_data.get("user")

        if block_id and user:
            try:
                Block.objects.get(uuid=block_id, user=user)
            except Block.DoesNotExist:
                raise ValidationError("Block not found")

        return block_id

    def clean_user(self) -> User:
        user = self.cleaned_data.get("user")
        if not user:
            raise ValidationError("User is required")
        return user
