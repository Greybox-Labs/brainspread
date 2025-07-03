from typing import List, Optional

from common.repositories.base_repository import BaseRepository

from ..models import AIModel, ChatMessage, ChatSession


class ChatMessageRepository(BaseRepository):
    model = ChatMessage

    @classmethod
    def add_message(
        cls,
        session: ChatSession,
        role: str,
        content: str,
        ai_model: Optional[AIModel] = None,
    ) -> ChatMessage:
        return cls.model.objects.create(
            session=session, role=role, content=content, ai_model=ai_model
        )

    @classmethod
    def get_messages(cls, session: ChatSession) -> List[ChatMessage]:
        return list(session.messages.order_by("created_at"))
