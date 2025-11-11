"""Repository interfaces (ports) for the domain layer."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import ChatSession


class ChatSessionRepository(ABC):
    """Interface for chat session persistence."""

    @abstractmethod
    def save(self, session: ChatSession) -> None:
        """Save a chat session."""
        pass

    @abstractmethod
    def get_by_id(self, chat_id: UUID) -> ChatSession | None:
        """Retrieve a chat session by ID."""
        pass

    @abstractmethod
    def get_all(self) -> list[ChatSession]:
        """Retrieve all chat sessions."""
        pass

    @abstractmethod
    def delete(self, chat_id: UUID) -> bool:
        """Delete a chat session."""
        pass

    @abstractmethod
    def exists(self, chat_id: UUID) -> bool:
        """Check if a chat session exists."""
        pass
