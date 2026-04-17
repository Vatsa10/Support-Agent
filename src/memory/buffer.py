from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from typing import List, Optional
from datetime import datetime


class SupportAgentMemory:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.sessions: dict = {}

    def get_memory(self, session_id: str) -> ConversationBufferMemory:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationBufferMemory(
                max_token_limit=2000, return_messages=True
            )
        return self.sessions[session_id]

    def add_user_message(self, session_id: str, message: str):
        memory = self.get_memory(session_id)
        memory.chat_memory.add_user_message(message)
        self._trim_history(session_id)

    def add_ai_message(self, session_id: str, message: str):
        memory = self.get_memory(session_id)
        memory.chat_memory.add_ai_message(message)
        self._trim_history(session_id)

    def get_conversation_history(self, session_id: str) -> List[dict]:
        memory = self.get_memory(session_id)
        messages = memory.chat_memory.messages
        return [
            {
                "role": "user" if m.type == "human" else "assistant",
                "content": m.content,
                "timestamp": getattr(m, "timestamp", datetime.now().isoformat()),
            }
            for m in messages
        ]

    def _trim_history(self, session_id: str):
        memory = self.get_memory(session_id)
        if len(memory.chat_memory.messages) > self.max_history * 2:
            memory.chat_memory.messages = memory.chat_memory.messages[
                -self.max_history * 2 :
            ]

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_formatted_history(self, session_id: str, last_n: int = 5) -> str:
        history = self.get_conversation_history(session_id)
        if not history:
            return ""

        recent = history[-last_n * 2 :] if len(history) > last_n * 2 else history

        formatted = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")

        return "\n".join(formatted)


agent_memory = SupportAgentMemory()
