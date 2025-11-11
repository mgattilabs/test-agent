import http
import logging
from datetime import datetime
from uuid import UUID, uuid4

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


def _analyze_conversation(chat_id: UUID) -> tuple[str | None, list[PBI], str]:
    """
    Analyze conversation to extract project and PBIs, and determine next action.

    Returns:
        tuple: (project, pbis, assistant_message)
    """
    session = chat_manager.get_session(chat_id)
    if not session or len(session.messages) == 0:
        return None, [], "Come posso aiutarti con l'estrazione di PBI?"

    # Get conversation history
    conversation = chat_manager.get_conversation_history(chat_id)

    # Try to extract project and PBIs
    request_id = str(uuid4())[:8]
    pbi_extractor = ExtractPBIModule()
    azdo_extractor = ExtractAzdoModule()
    pbi_extractor.set_lm(gemini_service.lm)
    azdo_extractor.set_lm(gemini_service.lm)

    try:
        logger.info(f"[{request_id}] Analyzing conversation for chat {chat_id}")
        project = azdo_extractor(summary=conversation)
        pbis = pbi_extractor(summary=conversation)

        logger.info(
            f"[{request_id}] Extracted project={project}, {len(pbis)} PBIs from chat {chat_id}"
        )

        # Update session with extracted data
        chat_manager.update_session_extraction(chat_id, project, pbis)

        # Determine what's missing and generate appropriate response
        if project is None:
            chat_manager.update_session_status(chat_id, "needs_info")
            return (
                None,
                [],
                "Non ho identificato il progetto Azure DevOps. Puoi specificare il nome del progetto?",
            )

        if len(pbis) == 0:
            chat_manager.update_session_status(chat_id, "needs_info")
            return (
                project,
                [],
                f"Ho identificato il progetto '{project}', ma non ho ancora informazioni sufficienti per creare PBI. Puoi descrivere le funzionalità o i requisiti che vuoi implementare?",
            )

        # We have both project and PBIs - ready for confirmation
        chat_manager.update_session_status(chat_id, "ready_for_confirmation")
        session.awaiting_confirmation = True

        pbi_summary = "\n".join([f"{i + 1}. {pbi.title}" for i, pbi in enumerate(pbis)])

        return (
            project,
            pbis,
            f"Perfetto! Ho identificato il progetto '{project}' e ho estratto {len(pbis)} PBI:\n\n{pbi_summary}\n\nVuoi che proceda con la creazione di questi PBI in Azure DevOps? (Usa l'endpoint /chat/sessions/{chat_id}/confirm per confermare)",
        )

    except Exception as e:
        logger.error(
            f"[{request_id}] Error analyzing conversation for chat {chat_id}: {e}",
            exc_info=True,
        )
        return (
            None,
            [],
            "Si è verificato un errore durante l'analisi della conversazione. Puoi fornire più dettagli?",
        )


# Request/Response Models
class PbiRequest(BaseModel):
    summary: str


class MessageResponse(BaseModel):
    message: str


class ChatSessionResponse(BaseModel):
    chat_id: UUID
    message: str


class AddMessageRequest(BaseModel):
    role: str
    content: str


class AddMessageResponse(BaseModel):
    message: str
    assistant_response: str | None = None
    needs_confirmation: bool = False
    session_status: str = "active"
    project: str | None = None
    pbi_count: int = 0


class ConfirmPBIRequest(BaseModel):
    confirm: bool


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
    request_id = str(uuid4())[:8]
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
async def get_chat_session(chat_id: UUID) -> ChatSession:
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


@app.post("/chat/sessions/{chat_id}/messages", response_model=AddMessageResponse)
async def add_message_to_chat(
    chat_id: UUID, request: AddMessageRequest
) -> AddMessageResponse:
    """
    Aggiunge un messaggio a una sessione di chat esistente.
    Se il messaggio è dall'utente, analizza automaticamente la conversazione
    per estrarre PBI e progetto, e genera una risposta appropriata.

    Args:
        chat_id: ID della sessione di chat
        request: Dati del messaggio (role e content)

    Returns:
        Risposta con eventuale messaggio dell'assistente e stato della sessione
    """
    try:
        message_role = MessageRole(request.role.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Ruolo non valido: {request.role}. Usa 'user', 'assistant' o 'system'.",
        )

    # Add the user's message
    message = chat_manager.add_message(chat_id, message_role, request.content)
    if not message:
        logger.warning(f"Chat session not found: {chat_id}")
        raise HTTPException(
            status_code=404, detail=f"Sessione di chat non trovata: {chat_id}"
        )

    logger.info(f"Added message to chat {chat_id} with role {request.role}")

    # If it's a user message, analyze the conversation and generate assistant response
    assistant_response = None
    session = chat_manager.get_session(chat_id)

    if message_role == MessageRole.USER and session:
        # Analyze conversation
        project, pbis, assistant_msg = _analyze_conversation(chat_id)
        assistant_response = assistant_msg

        # Add assistant response to the conversation
        chat_manager.add_message(chat_id, MessageRole.ASSISTANT, assistant_msg)

        # Get updated session to check status
        session = chat_manager.get_session(chat_id)

        return AddMessageResponse(
            message=f"Messaggio aggiunto alla chat {chat_id}",
            assistant_response=assistant_response,
            needs_confirmation=session.awaiting_confirmation if session else False,
            session_status=session.status if session else "active",
            project=session.project if session else None,
            pbi_count=len(session.pbis) if session else 0,
        )

    return AddMessageResponse(
        message=f"Messaggio aggiunto alla chat {chat_id} con ruolo {request.role}",
        session_status=session.status if session else "active",
    )


@app.post("/chat/sessions/{chat_id}/confirm", response_model=MessageResponse)
async def confirm_pbi_creation(
    chat_id: UUID, request: ConfirmPBIRequest
) -> MessageResponse:
    """
    Conferma o rifiuta la creazione dei PBI estratti dalla conversazione.

    Args:
        chat_id: ID della sessione di chat
        request: Richiesta di conferma (confirm: true/false)

    Returns:
        Risultato della conferma
    """
    session = chat_manager.get_session(chat_id)
    if not session:
        logger.warning(f"Chat session not found: {chat_id}")
        raise HTTPException(
            status_code=404, detail=f"Sessione di chat non trovata: {chat_id}"
        )

    if not session.awaiting_confirmation:
        raise HTTPException(
            status_code=400,
            detail="Questa sessione non è in attesa di conferma. Aggiungi prima un messaggio con i requisiti.",
        )

    if not request.confirm:
        # User rejected - reset status
        chat_manager.update_session_status(chat_id, "active")
        session.awaiting_confirmation = False
        chat_manager.add_message(
            chat_id,
            MessageRole.ASSISTANT,
            "Ok, nessun problema. Puoi modificare o aggiungere ulteriori requisiti.",
        )
        logger.info(f"User rejected PBI creation for chat {chat_id}")
        return MessageResponse(
            message="Creazione PBI annullata. Puoi continuare a modificare i requisiti."
        )

    # User confirmed - create PBIs
    if not session.project or len(session.pbis) == 0:
        raise HTTPException(
            status_code=400,
            detail="Mancano informazioni per creare i PBI. Progetto o PBI non identificati.",
        )

    try:
        # Create PBIs in Azure DevOps
        azdo_client.add_pbi(
            pbis=session.pbis,
            organization=env.azdo_organization,
            project=session.project,
        )

        # Update session status
        chat_manager.update_session_status(chat_id, "completed")
        session.awaiting_confirmation = False

        # Add confirmation message
        chat_manager.add_message(
            chat_id,
            MessageRole.ASSISTANT,
            f"Perfetto! Ho creato {len(session.pbis)} PBI nel progetto '{session.project}' in Azure DevOps.",
        )

        logger.info(
            f"Successfully created {len(session.pbis)} PBIs for chat {chat_id} in project {session.project}"
        )

        return MessageResponse(
            message=f"Creati con successo {len(session.pbis)} PBI nel progetto '{session.project}'."
        )

    except Exception as e:
        logger.error(
            f"Error creating PBIs for chat {chat_id}: {e}",
            exc_info=True,
        )
        chat_manager.update_session_status(chat_id, "error")
        chat_manager.add_message(
            chat_id,
            MessageRole.ASSISTANT,
            "Si è verificato un errore durante la creazione dei PBI. Riprova più tardi.",
        )
        raise HTTPException(
            status_code=500, detail=f"Errore durante la creazione dei PBI: {str(e)}"
        )


@app.delete("/chat/sessions/{chat_id}", response_model=MessageResponse)
async def delete_chat_session(chat_id: UUID) -> MessageResponse:
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
    chat_id: UUID, request: ProcessChatRequest
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

    request_id = str(uuid4())[:8]
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
