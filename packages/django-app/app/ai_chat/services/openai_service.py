class OpenAIService:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def send_message(self, messages):
        # Placeholder implementation; integrate OpenAI SDK here
        last_user = next((m for m in reversed(messages) if m["role"] == "user"), None)
        content = last_user["content"] if last_user else ""
        return f"Echo: {content}"
