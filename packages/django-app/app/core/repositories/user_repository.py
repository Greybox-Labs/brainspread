from typing import Any, Dict, Iterable, Optional

from common.repositories.base_repository import BaseRepository
from core.models import User


class UserRepository(BaseRepository):
    model = User

    @classmethod
    def get_by_filter(
        cls, filter_input: Optional[Dict[str, Any]] = None
    ) -> Iterable[User]:
        if filter_input:
            objects = cls.get_queryset().filter(**filter_input)
        else:
            objects = cls.get_queryset().all()
        return objects

    @classmethod
    def get_by_email(cls, email: str) -> Optional[User]:
        """Get user by email address"""
        try:
            return cls.get_queryset().get(email=email)
        except User.DoesNotExist:
            return None

    @classmethod
    def email_exists(cls, email: str) -> bool:
        """Check if user with email exists"""
        return cls.get_queryset().filter(email=email).exists()

    @classmethod
    def create(cls, data: Dict[str, Any]) -> User:
        user = cls.model.objects.create(**data)
        return user

    @classmethod
    def create_user(cls, email: str, password: str, **extra_fields: Any) -> User:
        """Create a new user with email and password"""
        return cls.model.objects.create_user(
            email=email, password=password, **extra_fields
        )

    @classmethod
    def update(
        cls, *, pk: Any = None, obj: Optional[User] = None, data: Dict[str, Any]
    ) -> User:
        user = obj or cls.get(pk=pk)

        if data.get("is_active"):
            user.is_active = data["is_active"]

        user.save()
        return user

    @classmethod
    def update_timezone(cls, user: User, timezone: str) -> User:
        """Update user's timezone"""
        user.timezone = timezone
        user.save(update_fields=["timezone"])
        return user

    @classmethod
    def update_theme(cls, user: User, theme: str) -> User:
        """Update user's theme preference"""
        user.theme = theme
        user.save(update_fields=["theme"])
        return user
