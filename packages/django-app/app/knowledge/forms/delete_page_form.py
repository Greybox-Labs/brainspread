from django import forms
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm

from ..models import Page


class DeletePageForm(BaseForm):
    page_id = forms.CharField(required=True)

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
