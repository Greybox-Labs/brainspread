from django import forms

from common.forms.base_form import BaseForm
from core.repositories import UserRepository


class GetHistoricalDataForm(BaseForm):
    days_back = forms.IntegerField(
        min_value=1, max_value=365, required=False, initial=30
    )
    limit = forms.IntegerField(min_value=1, max_value=100, required=False, initial=50)
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
