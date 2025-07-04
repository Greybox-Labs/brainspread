from django import forms

from core.models import User


class GetTagContentForm(forms.Form):
    """Form for getting tag content"""

    user = forms.ModelChoiceField(queryset=User.objects.all())
    tag_name = forms.CharField(max_length=50)

    def clean_tag_name(self):
        """Clean and validate tag name"""
        tag_name = self.cleaned_data["tag_name"]

        # Remove # prefix if present
        if tag_name.startswith("#"):
            tag_name = tag_name[1:]

        # Validate tag name format
        if not tag_name.replace("-", "").replace("_", "").isalnum():
            raise forms.ValidationError(
                "Tag name can only contain letters, numbers, hyphens, and underscores"
            )

        return tag_name
