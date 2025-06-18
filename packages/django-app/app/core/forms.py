from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
import pytz

from common.forms.base_form import BaseForm
from .repositories.user_repository import UserRepository


class LoginForm(BaseForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True)
    timezone = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(username=email, password=password)
            if not user or not user.is_active:
                raise ValidationError("Invalid credentials")
            cleaned_data["user"] = user

        return cleaned_data


class RegisterForm(BaseForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if UserRepository.email_exists(email):
            raise ValidationError("User with this email already exists")
        return email


class UpdateTimezoneForm(BaseForm):
    timezone = forms.CharField(required=True)

    def clean_timezone(self):
        timezone = self.cleaned_data.get("timezone")
        try:
            pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            pass
        return timezone
