from typing import Any, Optional, Type

from django.db import models
from django.db.models import QuerySet

from common.models.soft_delete_timestamp_mixin import SoftDeleteTimestampMixin

NOT_IMPLEMENTED_ERROR_MESSAGE = "You must define a `model` on the inheriting Repository"


class BaseRepository:
    model: Optional[Type[models.Model]] = None

    @classmethod
    def get(cls, *, pk: Any) -> Optional[models.Model]:
        if not cls.model:
            raise NotImplementedError(NOT_IMPLEMENTED_ERROR_MESSAGE)

        try:
            instance = cls.model.objects.get(pk=pk)
        except cls.model.DoesNotExist:
            return None

        return instance

    @classmethod
    def get_queryset(cls, queryset: Optional[QuerySet] = None) -> QuerySet:
        if queryset is None:
            if cls.model is None:
                raise NotImplementedError(NOT_IMPLEMENTED_ERROR_MESSAGE)

            if issubclass(cls.model, SoftDeleteTimestampMixin):
                return cls.model.objects.filter(is_active=True)

            return cls.model.objects.all()

        return queryset
