from django import forms

from common.forms.user_form import UserForm


class GetTagContentForm(UserForm):
    """Form for getting tag content command"""

    tag_name = forms.CharField(
        max_length=50, help_text="Name of the tag to retrieve content for"
    )

    def clean_tag_name(self) -> str:
        tag_name = self.cleaned_data.get("tag_name")
        if not tag_name:
            raise forms.ValidationError("Tag name is required")
        if not tag_name.strip():
            raise forms.ValidationError("Tag name cannot be empty")
        return tag_name.strip()
