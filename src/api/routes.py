"""API routes following clean architecture principles."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    get_add_message_use_case,
    get_confirm_pbi_use_case,
    get_create_session_use_case,
    get_delete_session_use_case,
    get_get_session_use_case,
    get_list_sessions_use_case,
)
from api.dtos import (
    AddMessageRequest,
    AddMessageResponse,
    ChatSessionDetailResponse,
    ChatSessionResponse,
    ChatSessionSummaryResponse,
    ConfirmPBIRequest,
    MessageResponse,
)
from api.mappers import (
    to_chat_session_detail_response,
    to_chat_session_summary_response,
)
from domain.entities import MessageRole
from use_cases.chat_session_use_cases import (
    AddMessageUseCase,
    ConfirmPBICreationUseCase,
    CreateChatSessionUseCase,
    DeleteChatSessionUseCase,
    GetChatSessionUseCase,
    ListChatSessionsUseCase,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat/sessions", tags=["Chat Sessions"])


@router.post("", response_model=ChatSessionResponse)
async def create_chat_session(
    use_case: CreateChatSessionUseCase = Depends(get_create_session_use_case),
) -> ChatSessionResponse:
    """Create a new chat session."""
    session = use_case.execute()
    return ChatSessionResponse(
        chat_id=session.chat_id,
        message=f"Sessione di chat creata con ID: {session.chat_id}",
    )


@router.get("", response_model=list[ChatSessionSummaryResponse])
async def list_chat_sessions(
    use_case: ListChatSessionsUseCase = Depends(get_list_sessions_use_case),
) -> list[ChatSessionSummaryResponse]:
    """List all chat sessions with summary information."""
    sessions = use_case.execute()
    logger.info(f"Listing {len(sessions)} chat sessions")
    return [to_chat_session_summary_response(s) for s in sessions]


@router.get("/{chat_id}", response_model=ChatSessionDetailResponse)
async def get_chat_session(
    chat_id: UUID,
    use_case: GetChatSessionUseCase = Depends(get_get_session_use_case),
) -> ChatSessionDetailResponse:
    """Get detailed information about a specific chat session."""
    session = use_case.execute(chat_id)
    if not session:
        raise HTTPException(
            status_code=404, detail=f"Sessione di chat non trovata: {chat_id}"
        )

    logger.info(f"Retrieved chat session: {chat_id}")
    return to_chat_session_detail_response(session)


@router.post("/{chat_id}/messages", response_model=AddMessageResponse)
async def add_message_to_chat(
    chat_id: UUID,
    request: AddMessageRequest,
    use_case: AddMessageUseCase = Depends(get_add_message_use_case),
) -> AddMessageResponse:
    """
    Add a message to a chat session.

    If the message is from a user, the system automatically analyzes
    the conversation and generates an assistant response.
    """
    try:
        role = MessageRole(request.role.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Ruolo non valido: {request.role}. Usa 'user', 'assistant' o 'system'.",
        )

    try:
        session, assistant_response = use_case.execute(chat_id, role, request.content)

        return AddMessageResponse(
            message=f"Messaggio aggiunto alla chat {chat_id}",
            assistant_response=assistant_response,
            needs_confirmation=session.awaiting_confirmation,
            session_status=session.status.value,
            project=session.project,
            pbi_count=len(session.pbis),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@router.post("/{chat_id}/confirm", response_model=MessageResponse)
async def confirm_pbi_creation(
    chat_id: UUID,
    request: ConfirmPBIRequest,
    use_case: ConfirmPBICreationUseCase = Depends(get_confirm_pbi_use_case),
) -> MessageResponse:
    """Confirm or reject PBI creation for a chat session."""
    try:
        success, message = use_case.execute(chat_id, request.confirm)
        return MessageResponse(message=message)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error confirming PBI creation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@router.delete("/{chat_id}", response_model=MessageResponse)
async def delete_chat_session(
    chat_id: UUID,
    use_case: DeleteChatSessionUseCase = Depends(get_delete_session_use_case),
) -> MessageResponse:
    """Delete a chat session."""
    success = use_case.execute(chat_id)
    if not success:
        raise HTTPException(
            status_code=404, detail=f"Sessione di chat non trovata: {chat_id}"
        )

    logger.info(f"Deleted chat session: {chat_id}")
    return MessageResponse(
        message=f"Sessione di chat {chat_id} eliminata con successo."
    )
