"""In-memory implementation of chat session repository."""

import logging
from uuid import UUID

from src.domain.entities import ChatSession
from src.domain.repositories import ChatSessionRepository

logger = logging.getLogger(__name__)


class InMemoryChatRepository(ChatSessionRepository):
    """In-memory storage for chat sessions."""

    def __init__(self):
        self._sessions: dict[UUID, ChatSession] = {}

    def save(self, session: ChatSession) -> None:
        """Save a chat session."""
        self._sessions[session.chat_id] = session
        logger.info(f"Saved chat session: {session.chat_id}")

    def get_by_id(self, chat_id: UUID) -> ChatSession | None:
        """Retrieve a chat session by ID."""
        return self._sessions.get(chat_id)

    def get_all(self) -> list[ChatSession]:
        """Retrieve all chat sessions."""
        return list(self._sessions.values())

    def delete(self, chat_id: UUID) -> bool:
        """Delete a chat session."""
        if chat_id in self._sessions:
            del self._sessions[chat_id]
            logger.info(f"Deleted chat session: {chat_id}")
            return True
        logger.warning(f"Chat session not found for deletion: {chat_id}")
        return False

    def exists(self, chat_id: UUID) -> bool:
        """Check if a chat session exists."""
        return chat_id in self._sessions
