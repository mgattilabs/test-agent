"""Domain entities representing core business concepts."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class MessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SessionStatus(str, Enum):
    """Status of a chat session."""

    ACTIVE = "active"
    NEEDS_INFO = "needs_info"
    READY_FOR_CONFIRMATION = "ready_for_confirmation"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class PBI:
    """Product Backlog Item."""

    title: str
    description: str

    def __post_init__(self):
        if not self.title or not self.title.strip():
            raise ValueError("PBI title cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("PBI description cannot be empty")


@dataclass
class ChatMessage:
    """Individual message in a chat session."""

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.content or not self.content.strip():
            raise ValueError("Message content cannot be empty")


@dataclass
class ChatSession:
    """
    Chat session containing conversation history.

    This is an aggregate root in DDD terms.
    """

    chat_id: UUID = field(default_factory=uuid4)
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    project: str | None = None
    pbis: list[PBI] = field(default_factory=list)
    status: SessionStatus = SessionStatus.ACTIVE
    awaiting_confirmation: bool = False

    def add_message(self, role: MessageRole, content: str) -> ChatMessage:
        """Add a message to the session."""
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message

    def update_extraction(self, project: str | None, pbis: list[PBI]) -> None:
        """Update session with extracted project and PBIs."""
        self.project = project
        self.pbis = pbis
        self.updated_at = datetime.now()

    def update_status(self, status: SessionStatus) -> None:
        """Update the session status."""
        self.status = status
        self.updated_at = datetime.now()

    def get_conversation_history(self) -> str:
        """Get formatted conversation history."""
        return "\n".join(f"{msg.role.value}: {msg.content}" for msg in self.messages)

    def is_ready_for_extraction(self) -> bool:
        """Check if session has enough messages for extraction."""
        return len(self.messages) > 0

    def needs_project_info(self) -> bool:
        """Check if project information is missing."""
        return self.project is None

    def needs_requirements(self) -> bool:
        """Check if requirements (PBIs) are missing."""
        return len(self.pbis) == 0

    def is_complete(self) -> bool:
        """Check if session has all required information."""
        return self.project is not None and len(self.pbis) > 0
