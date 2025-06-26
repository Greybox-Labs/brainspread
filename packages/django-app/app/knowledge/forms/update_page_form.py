from typing import Optional

from django import forms
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm
from core.models import User
from core.repositories import UserRepository

from ..models import Page


class UpdatePageForm(BaseForm):
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    page_id = forms.CharField(required=True)
    title = forms.CharField(max_length=200, required=False)
    content = forms.CharField(widget=forms.Textarea, required=False)
    slug = forms.SlugField(max_length=200, required=False)
    is_published = forms.BooleanField(required=False)

    def clean_page_id(self) -> str:
        page_id = self.cleaned_data.get("page_id")
        user = self.cleaned_data.get("user")

        # Validate page exists and belongs to user
        if page_id and user:
            try:
                Page.objects.get(uuid=page_id, user=user)
            except Page.DoesNotExist:
                raise ValidationError("Page not found")

        return page_id

    def clean_title(self) -> Optional[str]:
        title = self.cleaned_data.get("title")
        if title is not None:
            title = title.strip()
            if not title:
                raise ValidationError("Title cannot be empty")
        return title

    def clean_slug(self) -> Optional[str]:
        slug = self.cleaned_data.get("slug")
        page_id = self.cleaned_data.get("page_id")
        user = self.cleaned_data.get("user")

        if slug and user and page_id:
            # Check if new slug conflicts with existing pages (excluding current page)
            existing = Page.objects.filter(user=user, slug=slug).exclude(uuid=page_id)
            if existing.exists():
                raise ValidationError(f"Page with slug '{slug}' already exists")

        return slug

    def clean_user(self) -> User:
        user = self.cleaned_data.get("user")
        if not user:
            raise ValidationError("User is required")
        return user
