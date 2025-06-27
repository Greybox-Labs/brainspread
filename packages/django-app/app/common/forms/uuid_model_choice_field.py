import uuid
from typing import Any, Optional

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Model, QuerySet


class UUIDModelChoiceField(forms.Field):
    """
    A form field that accepts UUID strings and returns model instances.

    This field allows selecting models that inherit from UUIDModelMixin
    by their UUID string representation. It validates that the UUID exists
    in the provided queryset and returns the corresponding model instance.

    Usage:
        user = UUIDModelChoiceField(queryset=UserRepository.get_queryset())
    """

    def __init__(self, queryset: QuerySet, *args: Any, **kwargs: Any) -> None:
        self.queryset = queryset
        super().__init__(*args, **kwargs)

    def to_python(self, value: Any) -> Optional[Model]:
        """
        Convert the UUID string to a model instance.
        """
        # Handle empty values explicitly - this includes None, '', empty lists, etc.
        if value in self.empty_values or value is None or value == '':
            return None

        # If value is already a model instance of the correct type, return it
        if isinstance(value, self.queryset.model):
            return value

        # Convert string to UUID if needed
        if isinstance(value, str):
            # Handle empty string case
            if not value.strip():
                return None
            try:
                uuid_obj = uuid.UUID(value)
            except ValueError:
                raise ValidationError("Invalid UUID format.")
        elif isinstance(value, uuid.UUID):
            uuid_obj = value
        else:
            raise ValidationError("Value must be a UUID string, UUID object, or model instance.")

        # Look up the model instance by UUID
        try:
            return self.queryset.get(uuid=uuid_obj)
        except self.queryset.model.DoesNotExist:
            raise ValidationError(
                f"{self.queryset.model._meta.verbose_name} with UUID {uuid_obj} not found."
            )
        except self.queryset.model.MultipleObjectsReturned:
            raise ValidationError(
                f"Multiple {self.queryset.model._meta.verbose_name} objects found with UUID {uuid_obj}."
            )

    def validate(self, value: Any) -> None:
        """
        Validate that the value is a valid model instance from the queryset.
        """
        super().validate(value)

        if value is None and self.required:
            raise ValidationError("This field is required.")

        if value is not None and not isinstance(value, self.queryset.model):
            raise ValidationError(
                f"Expected {self.queryset.model._meta.verbose_name} instance."
            )
