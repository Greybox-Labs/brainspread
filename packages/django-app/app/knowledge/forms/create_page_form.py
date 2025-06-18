from django import forms
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm
from ..models import Page


class CreatePageForm(BaseForm):
    title = forms.CharField(max_length=200, required=True)
    content = forms.CharField(widget=forms.Textarea, required=False)
    slug = forms.SlugField(max_length=200, required=False)
    is_published = forms.BooleanField(required=False, initial=True)

    def __init__(self, data, user=None):
        self.user = user  # Only needed for slug validation
        super().__init__(data)

    def clean_title(self):
        title = self.cleaned_data.get("title")
        if title:
            title = title.strip()
            if not title:
                raise ValidationError("Title cannot be empty")
        return title

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if slug and self.user:
            # Check if slug already exists for this user
            if Page.objects.filter(user=self.user, slug=slug).exists():
                raise ValidationError(f"Page with slug '{slug}' already exists")
        return slug
