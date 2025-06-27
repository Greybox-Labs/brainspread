from typing import List

from common.repositories.base_repository import BaseRepository

from ..models import ChatMessage, ChatSession


class ChatMessageRepository(BaseRepository):
    model = ChatMessage

    @classmethod
    def add_message(cls, session: ChatSession, role: str, content: str) -> ChatMessage:
        return cls.model.objects.create(session=session, role=role, content=content)

    @classmethod
    def get_messages(cls, session: ChatSession) -> List[ChatMessage]:
        return list(session.messages.order_by("created_at"))
