from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class PBI(BaseModel):
    title: str
    description: str


class AgentResponse(BaseModel):
    action: str | None = None
    pbis: list[PBI] | None = None


class Azdo(BaseModel):
    project: str


class ActionResponse:
    @staticmethod
    def create_pbi_list() -> str:
        return "create_pbi_list"


class MessageRole(str, Enum):
    """Role of the message sender"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Individual message in a chat session"""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatSession(BaseModel):
    """Chat session containing conversation history"""

    chat_id: UUID
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    project: str | None = None
    pbis: list[PBI] = Field(default_factory=list)
    status: str = "active"  # active, needs_info, ready_for_confirmation, confirmed, completed, error
    awaiting_confirmation: bool = False


class ChatSessionSummary(BaseModel):
    """Summary information about a chat session"""

    chat_id: UUID
    message_count: int
    created_at: datetime
    updated_at: datetime
    project: str | None = None
    pbi_count: int
    status: str
