"""Mappers to convert between domain entities and API DTOs."""

from src.api.dtos import (
    ChatMessageResponse,
    ChatSessionDetailResponse,
    ChatSessionSummaryResponse,
    PBIResponse,
)
from src.domain.entities import ChatSession


def to_chat_session_detail_response(session: ChatSession) -> ChatSessionDetailResponse:
    """Convert domain ChatSession to API response."""
    return ChatSessionDetailResponse(
        chat_id=session.chat_id,
        messages=[
            ChatMessageResponse(
                role=msg.role.value, content=msg.content, timestamp=msg.timestamp
            )
            for msg in session.messages
        ],
        created_at=session.created_at,
        updated_at=session.updated_at,
        project=session.project,
        pbis=[
            PBIResponse(title=pbi.title, description=pbi.description)
            for pbi in session.pbis
        ],
        status=session.status.value,
        awaiting_confirmation=session.awaiting_confirmation,
    )


def to_chat_session_summary_response(
    session: ChatSession,
) -> ChatSessionSummaryResponse:
    """Convert domain ChatSession to summary response."""
    return ChatSessionSummaryResponse(
        chat_id=session.chat_id,
        message_count=len(session.messages),
        created_at=session.created_at,
        updated_at=session.updated_at,
        project=session.project,
        pbi_count=len(session.pbis),
        status=session.status.value,
    )
