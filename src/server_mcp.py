import logging
import uuid
from datetime import datetime

from fastmcp import FastMCP

from extractors.pbi import ExtractPBIModule
from models import PBI, MessageRole
from src import azdo_client, llm_client
from src.chat_manager import ChatManager
from src.config import settings
from src.extractors.azdo import ExtractAzdoModule

logger = logging.getLogger(__name__)

request_log = []
chat_manager = ChatManager()
mcp = FastMCP(name="azdo-server")


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


@mcp.tool()
def create_chat_session() -> str:
    """
    Crea una nuova sessione di chat per la gestione di conversazioni.
    Restituisce il chat_id della nuova sessione.
    """
    session = chat_manager.create_session()
    return f"Sessione di chat creata con ID: {session.chat_id}"


@mcp.tool()
def list_chat_sessions() -> str:
    """
    Elenca tutte le sessioni di chat attive con informazioni riassuntive.
    Restituisce una lista di chat_id con dettagli.
    """
    sessions = chat_manager.list_sessions()
    if not sessions:
        return "Nessuna sessione di chat trovata."

    result_lines = ["Sessioni di chat attive:"]
    for session in sessions:
        result_lines.append(
            f"- Chat ID: {session.chat_id}"
            f" | Messaggi: {session.message_count}"
            f" | Progetto: {session.project or 'N/A'}"
            f" | PBI: {session.pbi_count}"
            f" | Status: {session.status}"
            f" | Creato: {session.created_at.isoformat()}"
        )

    return "\n".join(result_lines)


@mcp.tool()
def add_message_to_chat(chat_id: str, role: str, content: str) -> str:
    """
    Aggiunge un messaggio a una sessione di chat esistente.

    Args:
        chat_id: ID della sessione di chat
        role: Ruolo del mittente ('user', 'assistant', 'system')
        content: Contenuto del messaggio

    Returns:
        Conferma dell'aggiunta del messaggio
    """
    try:
        message_role = MessageRole(role.lower())
    except ValueError:
        return f"Ruolo non valido: {role}. Usa 'user', 'assistant' o 'system'."

    message = chat_manager.add_message(chat_id, message_role, content)
    if not message:
        return f"Sessione di chat non trovata: {chat_id}"

    return f"Messaggio aggiunto alla chat {chat_id} con ruolo {role}"


@mcp.tool()
def get_chat_session(chat_id: str) -> str:
    """
    Ottiene i dettagli di una sessione di chat specifica.

    Args:
        chat_id: ID della sessione di chat

    Returns:
        Dettagli completi della sessione inclusa la cronologia dei messaggi
    """
    session = chat_manager.get_session(chat_id)
    if not session:
        return f"Sessione di chat non trovata: {chat_id}"

    lines = [
        f"Chat ID: {session.chat_id}",
        f"Status: {session.status}",
        f"Progetto: {session.project or 'Non identificato'}",
        f"PBI estratti: {len(session.pbis)}",
        f"Creato: {session.created_at.isoformat()}",
        f"Ultimo aggiornamento: {session.updated_at.isoformat()}",
        f"\nCronologia messaggi ({len(session.messages)} messaggi):",
    ]

    for i, msg in enumerate(session.messages, 1):
        lines.append(
            f"{i}. [{msg.role.value}] {msg.timestamp.strftime('%H:%M:%S')}: {msg.content}"
        )

    return "\n".join(lines)


@mcp.tool()
def delete_chat_session(chat_id: str) -> str:
    """
    Elimina una sessione di chat.

    Args:
        chat_id: ID della sessione di chat da eliminare

    Returns:
        Conferma dell'eliminazione
    """
    success = chat_manager.delete_session(chat_id)
    if success:
        return f"Sessione di chat {chat_id} eliminata con successo."
    return f"Sessione di chat non trovata: {chat_id}"


@mcp.tool()
def process_chat_session(chat_id: str, create_pbis: bool = True) -> str:
    """
    Analizza la cronologia di una chat per estrarre PBI e progetto Azure DevOps.
    Opzionalmente crea i PBI in Azure DevOps.

    Args:
        chat_id: ID della sessione di chat da processare
        create_pbis: Se True, crea i PBI in Azure DevOps (default: True)

    Returns:
        Risultato dell'elaborazione con dettagli sui PBI estratti
    """
    session = chat_manager.get_session(chat_id)
    if not session:
        return f"Sessione di chat non trovata: {chat_id}"

    if len(session.messages) == 0:
        return f"La sessione di chat {chat_id} non contiene messaggi."

    # Update status to processing
    chat_manager.update_session_status(chat_id, "processing")

    request_id = str(uuid.uuid4())[:8]
    envSettings = settings.EnvironmentSettings()
    gemini_lm = llm_client.GeminiService(envSettings.gemini_api_key)
    pbi_extractor = ExtractPBIModule()
    azdo_extractor = ExtractAzdoModule()
    pbi_extractor.set_lm(gemini_lm.lm)
    azdo_extractor.set_lm(gemini_lm.lm)

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
            return f"Nessun PBI estratto dalla conversazione nella chat {chat_id}."

        if project is None:
            chat_manager.update_session_status(chat_id, "error")
            logger.warning(
                f"[{request_id}] Progetto Azure DevOps non identificato nella chat {chat_id}"
            )
            return f"Progetto Azure DevOps non identificato nella conversazione. Estratti {len(pbis)} PBI ma non possono essere creati senza progetto."

        # Create PBIs in Azure DevOps if requested
        if create_pbis:
            azdo_client.add_pbi(
                pbis=pbis,
                organization=envSettings.azdo_organization,
                project=project,
            )
            chat_manager.update_session_status(chat_id, "completed")
            return f"Elaborazione completata per chat {chat_id}. Estratti e creati {len(pbis)} PBI nel progetto '{project}'."
        else:
            chat_manager.update_session_status(chat_id, "completed")
            return f"Elaborazione completata per chat {chat_id}. Estratti {len(pbis)} PBI nel progetto '{project}' (non creati in Azure DevOps)."

    except Exception as e:
        logger.error(
            f"[{request_id}] Errore durante l'elaborazione della chat {chat_id}: {e}",
            exc_info=True,
        )
        chat_manager.update_session_status(chat_id, "error")
        _log_request(request_id, conversation, None, [], "error")
        return f"Errore durante l'elaborazione della chat {chat_id}: {str(e)}"


@mcp.tool()
def process_azdo_summary(summary: str) -> str:
    """
    Elabora un riassunto direttamente per estrarre e creare PBI in Azure DevOps.
    Per conversazioni interattive, usa invece le funzioni di gestione chat.
    """
    request_id = str(uuid.uuid4())[:8]
    envSettings = settings.EnvironmentSettings()
    gemini_lm = llm_client.GeminiService(envSettings.gemini_api_key)
    pbi_extractor = ExtractPBIModule()
    azdo_extractor = ExtractAzdoModule()
    pbi_extractor.set_lm(gemini_lm.lm)
    azdo_extractor.set_lm(gemini_lm.lm)

    logger.info(f"[{request_id}] Processing Azure DevOps summary: {summary[:100]}...")

    try:
        project = azdo_extractor(summary=summary)
        pbis = pbi_extractor(summary=summary)
        logger.info(f"[{request_id}] Estratti {len(pbis)} PBI dal sommario")

        _log_request(request_id, summary, project, pbis, "success")

        if len(pbis) == 0:
            logger.warning(f"[{request_id}] Nessun PBI estratto dal sommario.")
            return "Nessun PBI estratto dal sommario fornito."

        if project is None:
            logger.warning(f"[{request_id}] Progetto Azure DevOps non identificato.")
            return "Progetto Azure DevOps non identificato nel sommario."

        azdo_client.add_pbi(
            pbis=pbis,
            organization=envSettings.azdo_organization,
            project=project,
        )
        return (
            f"Elaborazione completata. Creati {len(pbis)} PBI nel progetto '{project}'."
        )
    except Exception as e:
        logger.error(
            f"[{request_id}] Errore durante l'estrazione dei PBI: {e}", exc_info=True
        )
        _log_request(request_id, summary, None, [], "error")
        raise e


def main():
    logger.info("Starting MCP server...")
    mcp.run()


if __name__ == "__main__":
    main()
