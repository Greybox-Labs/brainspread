from typing import Dict, List

from common.commands.abstract_base_command import AbstractBaseCommand

from ai_chat.repositories.chat_repository import ChatRepository
from ai_chat.services.openai_service import OpenAIService


class SendMessageCommand(AbstractBaseCommand):
    def __init__(self, user, session, message: str, api_key: str) -> None:
        self.user = user
        self.session = session
        self.message = message
        self.api_key = api_key

    def execute(self) -> Dict[str, str]:
        super().execute()

        if not self.session:
            self.session = ChatRepository.create_session(self.user)

        ChatRepository.add_message(self.session, "user", self.message)

        service = OpenAIService(self.api_key)
        messages: List[Dict[str, str]] = [
            {"role": msg.role, "content": msg.content}
            for msg in ChatRepository.get_messages(self.session)
        ]
        response_content = service.send_message(messages)

        ChatRepository.add_message(self.session, "assistant", response_content)

        return {"response": response_content}
