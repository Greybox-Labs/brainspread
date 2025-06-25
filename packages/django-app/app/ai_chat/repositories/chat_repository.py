from typing import List

from ai_chat.models import ChatMessage, ChatSession


class ChatRepository:
    @staticmethod
    def create_session(user) -> ChatSession:
        return ChatSession.objects.create(user=user)

    @staticmethod
    def add_message(session: ChatSession, role: str, content: str) -> ChatMessage:
        return ChatMessage.objects.create(session=session, role=role, content=content)

    @staticmethod
    def get_messages(session: ChatSession) -> List[ChatMessage]:
        return list(session.messages.order_by("created_at"))
