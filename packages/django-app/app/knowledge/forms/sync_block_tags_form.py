from django import forms

from common.forms.uuid_model_choice_field import UUIDModelChoiceField
from core.models import User

from ..models import Block


class SyncBlockTagsForm(forms.Form):
    """Form for synchronizing block tags based on content"""

    block = UUIDModelChoiceField(queryset=Block.objects.all())
    content = forms.CharField(required=False, widget=forms.Textarea)
    user = forms.ModelChoiceField(queryset=User.objects.all())

    def clean(self):
        cleaned_data = super().clean()
        block = cleaned_data.get("block")
        user = cleaned_data.get("user")

        # Ensure user owns the block
        if block and user and block.user != user:
            raise forms.ValidationError(
                "User does not have permission to modify this block"
            )

        return cleaned_data
