import http
import logging
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import azdo_client
from chat_manager import ChatManager
from config.settings import EnvironmentSettings
from extractors import ExtractPBIModule
from extractors.azdo import ExtractAzdoModule
from llm_client import GeminiService
from models import ChatSession, ChatSessionSummary, MessageRole, PBI

logger = logging.getLogger(__name__)

app = FastAPI(title="Azure DevOps PBI Extraction API", version="1.0.0")
env = EnvironmentSettings()
gemini_service = GeminiService(env.gemini_api_key)
chat_manager = ChatManager()
request_log = []


def _log_request(
    request_id: str,
    summary: str,
    project: str | None,
    pbis: list[PBI],
    status: str = "success",
):
    if any(log["request_id"] == request_id for log in request_log):
        for log in request_log:
            if log["request_id"] == request_id:
                log["status"] = status
                log["pbis"] = pbis
                log["project"] = project
                logger.info(f"Request status updated: {log}")
                return

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "summary_preview": summary[:100],
        "project": project,
        "pbis": pbis,
        "status": status,
    }
    request_log.append(log_entry)
    logger.info(f"Request logged: {log_entry}")


# Request/Response Models
class PbiRequest(BaseModel):
    summary: str


class MessageResponse(BaseModel):
    message: str


class ChatSessionResponse(BaseModel):
    chat_id: str
    message: str


class AddMessageRequest(BaseModel):
    role: str
    content: str


class ProcessChatRequest(BaseModel):
    create_pbis: bool = True


# Legacy endpoint (kept for backward compatibility)
@app.post("/pbi-creator", response_model=MessageResponse)
async def pbi_creator(
    request: PbiRequest, status_code=http.HTTPStatus.OK
) -> MessageResponse:
    """
    Legacy endpoint for direct PBI extraction from summary.
    For interactive conversations, use the chat session endpoints.
    """
    request_id = str(uuid.uuid4())[:8]
    pbi_extractor = ExtractPBIModule()
    azdo_extractor = ExtractAzdoModule()
    pbi_extractor.set_lm(gemini_service.lm)
    azdo_extractor.set_lm(gemini_service.lm)

    logger.info(f"[{request_id}] Processing summary: {request.summary[:100]}...")

    try:
        project = azdo_extractor(summary=request.summary)
        pbis = pbi_extractor(summary=request.summary)
        logger.info(f"[{request_id}] Estratti {len(pbis)} PBI dal sommario")

        _log_request(request_id, request.summary, project, pbis, "success")

        if len(pbis) == 0:
            logger.warning(f"[{request_id}] Nessun PBI estratto dal sommario.")
            return MessageResponse(message="Nessun PBI estratto dal sommario fornito.")

        if project is None:
            logger.warning(f"[{request_id}] Progetto Azure DevOps non identificato.")
            return MessageResponse(
                message="Progetto Azure DevOps non identificato nel sommario."
            )

        azdo_client.add_pbi(
            pbis=pbis,
            organization=env.azdo_organization,
            project=project,
        )
        return MessageResponse(
            message=f"Elaborazione completata. Creati {len(pbis)} PBI nel progetto '{project}'."
        )
    except Exception as e:
        logger.error(
            f"[{request_id}] Errore durante l'estrazione dei PBI: {e}", exc_info=True
        )
        _log_request(request_id, request.summary, None, [], "error")
        raise HTTPException(status_code=500, detail=str(e))


# Chat Session Endpoints
@app.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session() -> ChatSessionResponse:
    """
    Crea una nuova sessione di chat per la gestione di conversazioni.
    Restituisce il chat_id della nuova sessione.
    """
    session = chat_manager.create_session()
    logger.info(f"Created chat session: {session.chat_id}")
    return ChatSessionResponse(
        chat_id=session.chat_id,
        message=f"Sessione di chat creata con ID: {session.chat_id}",
    )


@app.get("/chat/sessions", response_model=list[ChatSessionSummary])
async def list_chat_sessions() -> list[ChatSessionSummary]:
    """
    Elenca tutte le sessioni di chat attive con informazioni riassuntive.
    Restituisce una lista di sessioni con dettagli.
    """
    sessions = chat_manager.list_sessions()
    logger.info(f"Listing {len(sessions)} chat sessions")
    return sessions


@app.get("/chat/sessions/{chat_id}", response_model=ChatSession)
async def get_chat_session(chat_id: str) -> ChatSession:
    """
    Ottiene i dettagli di una sessione di chat specifica.

    Args:
        chat_id: ID della sessione di chat

    Returns:
        Dettagli completi della sessione inclusa la cronologia dei messaggi
    """
    session = chat_manager.get_session(chat_id)
    if not session:
        logger.warning(f"Chat session not found: {chat_id}")
        raise HTTPException(
            status_code=404, detail=f"Sessione di chat non trovata: {chat_id}"
        )

    logger.info(f"Retrieved chat session: {chat_id}")
    return session


@app.post("/chat/sessions/{chat_id}/messages", response_model=MessageResponse)
async def add_message_to_chat(
    chat_id: str, request: AddMessageRequest
) -> MessageResponse:
    """
    Aggiunge un messaggio a una sessione di chat esistente.

    Args:
        chat_id: ID della sessione di chat
        request: Dati del messaggio (role e content)

    Returns:
        Conferma dell'aggiunta del messaggio
    """
    try:
        message_role = MessageRole(request.role.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Ruolo non valido: {request.role}. Usa 'user', 'assistant' o 'system'.",
        )

    message = chat_manager.add_message(chat_id, message_role, request.content)
    if not message:
        logger.warning(f"Chat session not found: {chat_id}")
        raise HTTPException(
            status_code=404, detail=f"Sessione di chat non trovata: {chat_id}"
        )

    logger.info(f"Added message to chat {chat_id} with role {request.role}")
    return MessageResponse(
        message=f"Messaggio aggiunto alla chat {chat_id} con ruolo {request.role}"
    )


@app.delete("/chat/sessions/{chat_id}", response_model=MessageResponse)
async def delete_chat_session(chat_id: str) -> MessageResponse:
    """
    Elimina una sessione di chat.

    Args:
        chat_id: ID della sessione di chat da eliminare

    Returns:
        Conferma dell'eliminazione
    """
    success = chat_manager.delete_session(chat_id)
    if not success:
        logger.warning(f"Chat session not found for deletion: {chat_id}")
        raise HTTPException(
            status_code=404, detail=f"Sessione di chat non trovata: {chat_id}"
        )

    logger.info(f"Deleted chat session: {chat_id}")
    return MessageResponse(
        message=f"Sessione di chat {chat_id} eliminata con successo."
    )


@app.post("/chat/sessions/{chat_id}/process", response_model=MessageResponse)
async def process_chat_session(
    chat_id: str, request: ProcessChatRequest
) -> MessageResponse:
    """
    Analizza la cronologia di una chat per estrarre PBI e progetto Azure DevOps.
    Opzionalmente crea i PBI in Azure DevOps.

    Args:
        chat_id: ID della sessione di chat da processare
        request: Parametri di processamento (create_pbis)

    Returns:
        Risultato dell'elaborazione con dettagli sui PBI estratti
    """
    session = chat_manager.get_session(chat_id)
    if not session:
        logger.warning(f"Chat session not found: {chat_id}")
        raise HTTPException(
            status_code=404, detail=f"Sessione di chat non trovata: {chat_id}"
        )

    if len(session.messages) == 0:
        raise HTTPException(
            status_code=400,
            detail=f"La sessione di chat {chat_id} non contiene messaggi.",
        )

    # Update status to processing
    chat_manager.update_session_status(chat_id, "processing")

    request_id = str(uuid.uuid4())[:8]
    pbi_extractor = ExtractPBIModule()
    azdo_extractor = ExtractAzdoModule()
    pbi_extractor.set_lm(gemini_service.lm)
    azdo_extractor.set_lm(gemini_service.lm)

    # Get conversation history
    conversation = chat_manager.get_conversation_history(chat_id)
    logger.info(
        f"[{request_id}] Processing chat session {chat_id} with {len(session.messages)} messages"
    )

    try:
        # Extract project and PBIs from conversation
        project = azdo_extractor(summary=conversation)
        pbis = pbi_extractor(summary=conversation)
        logger.info(f"[{request_id}] Estratti {len(pbis)} PBI dalla chat {chat_id}")

        # Update session with extraction results
        chat_manager.update_session_extraction(chat_id, project, pbis)

        _log_request(request_id, conversation, project, pbis, "success")

        if len(pbis) == 0:
            chat_manager.update_session_status(chat_id, "completed")
            logger.warning(f"[{request_id}] Nessun PBI estratto dalla chat {chat_id}")
            return MessageResponse(
                message=f"Nessun PBI estratto dalla conversazione nella chat {chat_id}."
            )

        if project is None:
            chat_manager.update_session_status(chat_id, "error")
            logger.warning(
                f"[{request_id}] Progetto Azure DevOps non identificato nella chat {chat_id}"
            )
            return MessageResponse(
                message=f"Progetto Azure DevOps non identificato nella conversazione. Estratti {len(pbis)} PBI ma non possono essere creati senza progetto."
            )

        # Create PBIs in Azure DevOps if requested
        if request.create_pbis:
            azdo_client.add_pbi(
                pbis=pbis,
                organization=env.azdo_organization,
                project=project,
            )
            chat_manager.update_session_status(chat_id, "completed")
            return MessageResponse(
                message=f"Elaborazione completata per chat {chat_id}. Estratti e creati {len(pbis)} PBI nel progetto '{project}'."
            )
        else:
            chat_manager.update_session_status(chat_id, "completed")
            return MessageResponse(
                message=f"Elaborazione completata per chat {chat_id}. Estratti {len(pbis)} PBI nel progetto '{project}' (non creati in Azure DevOps)."
            )

    except Exception as e:
        logger.error(
            f"[{request_id}] Errore durante l'elaborazione della chat {chat_id}: {e}",
            exc_info=True,
        )
        chat_manager.update_session_status(chat_id, "error")
        _log_request(request_id, conversation, None, [], "error")
        raise HTTPException(status_code=500, detail=str(e))
