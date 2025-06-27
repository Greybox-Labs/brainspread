from common.repositories.base_repository import BaseRepository
from core.models import User

from ..models import ChatSession


class ChatSessionRepository(BaseRepository):
    model = ChatSession

    @classmethod
    def create_session(cls, user: User) -> ChatSession:
        return cls.model.objects.create(user=user)
