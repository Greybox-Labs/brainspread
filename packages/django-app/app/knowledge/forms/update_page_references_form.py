from django import forms

from common.forms.uuid_model_choice_field import UUIDModelChoiceField
from core.models import User

from ..models import Page


class UpdatePageReferencesForm(forms.Form):
    """Form for updating page references when a page's title or slug changes"""

    page = UUIDModelChoiceField(queryset=Page.objects.all())
    old_title = forms.CharField(max_length=200, required=False)
    old_slug = forms.SlugField(max_length=200, required=False)
    user = forms.ModelChoiceField(queryset=User.objects.all())

    def clean(self):
        cleaned_data = super().clean()
        page = cleaned_data.get("page")
        user = cleaned_data.get("user")
        old_title = cleaned_data.get("old_title")
        old_slug = cleaned_data.get("old_slug")

        # Ensure user owns the page
        if page and user and page.user != user:
            raise forms.ValidationError(
                "User does not have permission to modify this page"
            )

        # At least one of old_title or old_slug should be provided
        if not old_title and not old_slug:
            raise forms.ValidationError(
                "At least one of old_title or old_slug must be provided"
            )

        return cleaned_data
