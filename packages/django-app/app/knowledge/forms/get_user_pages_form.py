from django import forms

from common.forms.base_form import BaseForm


class GetUserPagesForm(BaseForm):
    published_only = forms.BooleanField(required=False, initial=True)
    limit = forms.IntegerField(min_value=1, max_value=100, required=False, initial=10)
    offset = forms.IntegerField(min_value=0, required=False, initial=0)