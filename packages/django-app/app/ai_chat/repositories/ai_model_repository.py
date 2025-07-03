from typing import Optional

from common.repositories.base_repository import BaseRepository

from ..models import AIModel


class AIModelRepository(BaseRepository):
    model = AIModel

    @classmethod
    def get_by_name(cls, name: str) -> Optional[AIModel]:
        """Get AI model by name."""
        try:
            return cls.model.objects.get(name=name, is_active=True)
        except cls.model.DoesNotExist:
            return None
