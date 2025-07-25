import pytz
from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm
from core.repositories.user_repository import UserRepository


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
    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    timezone = forms.CharField(required=True)

    def clean_timezone(self):
        timezone = self.cleaned_data.get("timezone")
        try:
            pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            pass
        return timezone


class UpdateThemeForm(BaseForm):
    THEME_CHOICES = [
        ("dark", "Dark"),
        ("light", "Light"),
        ("solarized_dark", "Solarized Dark"),
        ("purple", "Purple"),
        ("earthy", "Earthy"),
        ("forest", "Forest"),
    ]

    user = forms.ModelChoiceField(queryset=UserRepository.get_queryset())
    theme = forms.ChoiceField(choices=THEME_CHOICES, required=True)

    def clean_theme(self):
        theme = self.cleaned_data.get("theme")
        valid_themes = ["dark", "light", "solarized_dark", "purple", "earthy", "forest"]
        if theme not in valid_themes:
            raise ValidationError("Invalid theme choice")
        return theme
