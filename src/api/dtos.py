"""Data Transfer Objects for API layer."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ChatSessionResponse(BaseModel):
    """Response for chat session creation."""

    chat_id: UUID
    message: str


class AddMessageRequest(BaseModel):
    """Request to add a message to chat."""

    role: str
    content: str


class AddMessageResponse(BaseModel):
    """Response after adding a message."""

    message: str
    assistant_response: str | None = None
    needs_confirmation: bool = False
    session_status: str = "active"
    project: str | None = None
    pbi_count: int = 0


class ConfirmPBIRequest(BaseModel):
    """Request to confirm PBI creation."""

    confirm: bool


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class PBIResponse(BaseModel):
    """PBI representation in API."""

    title: str
    description: str


class ChatMessageResponse(BaseModel):
    """Chat message representation in API."""

    role: str
    content: str
    timestamp: datetime


class ChatSessionDetailResponse(BaseModel):
    """Detailed chat session response."""

    chat_id: UUID
    messages: list[ChatMessageResponse]
    created_at: datetime
    updated_at: datetime
    project: str | None = None
    pbis: list[PBIResponse]
    status: str
    awaiting_confirmation: bool


class ChatSessionSummaryResponse(BaseModel):
    """Summary of a chat session."""

    chat_id: UUID
    message_count: int
    created_at: datetime
    updated_at: datetime
    project: str | None = None
    pbi_count: int
    status: str
