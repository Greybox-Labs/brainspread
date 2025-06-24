from typing import TypedDict

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models.crud_timestamps_mixin import CRUDTimestampsMixin
from common.models.soft_delete_timestamp_mixin import SoftDeleteTimestampMixin
from common.models.uuid_mixin import UUIDModelMixin
from core.managers import UserManager


class User(
    UUIDModelMixin,
    CRUDTimestampsMixin,
    SoftDeleteTimestampMixin,
    AbstractBaseUser,
    PermissionsMixin,
):
    USERNAME_FIELD = "email"
    objects = UserManager()

    email = models.EmailField(
        verbose_name="email",
        max_length=255,
        unique=True,
    )

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )

    timezone = models.CharField(
        _("timezone"),
        max_length=50,
        default="UTC",
        help_text=_("User's preferred timezone (e.g., America/New_York, UTC, etc.)"),
    )

    THEME_CHOICES = [
        ("dark", "Dark"),
        ("light", "Light"),
    ]

    theme = models.CharField(
        _("theme"),
        max_length=10,
        choices=THEME_CHOICES,
        default="dark",
        help_text=_("User's preferred theme (dark or light)"),
    )

    def __str__(self):
        return self.email

    class Meta:
        db_table = "users"
        default_permissions = ()
        unique_together = []
        ordering = ("id",)


# API response type for User data
class UserData(TypedDict):
    uuid: str
    email: str
    is_active: bool
    timezone: str
    theme: str
    date_joined: str
