from django import forms
from django.core.exceptions import ValidationError

from common.forms.base_form import BaseForm

from .models import ChatSession
from .repositories.user_settings_repository import UserSettingsRepository


class SendMessageForm(BaseForm):
    message = forms.CharField(
        required=False
    )  # We'll handle validation in clean_message
    model = forms.CharField(required=True)  # Model selection per request
    session_id = forms.CharField(required=False)
    context_blocks = forms.JSONField(required=False)

    def __init__(self, data, user=None):
        self.user = user
        super().__init__(data)

    def clean_message(self):
        message = self.cleaned_data.get("message")
        if not message or not message.strip():
            raise ValidationError("Message cannot be empty")
        return message.strip()

    def clean_session_id(self):
        session_id = self.cleaned_data.get("session_id")
        if session_id and self.user:
            try:
                session = ChatSession.objects.get(uuid=session_id, user=self.user)
                return session
            except ChatSession.DoesNotExist:
                # Return None for non-existent sessions - let the command create a new one
                return None
        return None

    def clean_context_blocks(self):
        context_blocks = self.cleaned_data.get("context_blocks")
        if context_blocks is None:
            return []

        if not isinstance(context_blocks, list):
            raise ValidationError("Context blocks must be a list")

        return context_blocks

    def clean(self):
        cleaned_data = super().clean()

        if not self.user:
            raise ValidationError("User is required")

        # Get model and validate it exists in our database
        model_name = cleaned_data.get("model")
        if not model_name:
            raise ValidationError("Model is required.")

        # Look up the model in our database
        from .models import AIModel

        try:
            ai_model = AIModel.objects.select_related("provider").get(
                name=model_name, is_active=True
            )
        except AIModel.DoesNotExist:
            raise ValidationError(
                f"Model '{model_name}' is not available or not found."
            )

        # Get the provider and check API key
        provider = ai_model.provider
        provider_name = provider.name.lower()

        # Check API key for the provider
        user_settings_repo = UserSettingsRepository()
        api_key = user_settings_repo.get_api_key(self.user, provider)
        if not api_key:
            raise ValidationError(
                f"No API key configured for {provider.name}. Please add your API key in settings."
            )

        # Add validated data to cleaned_data
        cleaned_data["ai_model"] = ai_model
        cleaned_data["provider"] = provider
        cleaned_data["provider_name"] = provider_name
        cleaned_data["api_key"] = api_key

        return cleaned_data
