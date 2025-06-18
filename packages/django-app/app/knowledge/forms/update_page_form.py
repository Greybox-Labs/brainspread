from django import forms
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm
from ..models import Page


class UpdatePageForm(BaseForm):
    page_id = forms.CharField(required=True)
    title = forms.CharField(max_length=200, required=False)
    content = forms.CharField(widget=forms.Textarea, required=False)
    slug = forms.SlugField(max_length=200, required=False)
    is_published = forms.BooleanField(required=False)

    def __init__(self, data, user=None):
        self.user = user  # Only needed for validation
        super().__init__(data)

    def clean_page_id(self):
        page_id = self.cleaned_data.get("page_id")

        # Validate page exists and belongs to user
        if page_id and self.user:
            try:
                Page.objects.get(uuid=page_id, user=self.user)
            except Page.DoesNotExist:
                raise ValidationError("Page not found")

        return page_id

    def clean_title(self):
        title = self.cleaned_data.get("title")
        if title is not None:
            title = title.strip()
            if not title:
                raise ValidationError("Title cannot be empty")
        return title

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        page_id = self.cleaned_data.get("page_id")

        if slug and self.user and page_id:
            # Check if new slug conflicts with existing pages (excluding current page)
            existing = Page.objects.filter(user=self.user, slug=slug).exclude(
                uuid=page_id
            )
            if existing.exists():
                raise ValidationError(f"Page with slug '{slug}' already exists")

        return slug
