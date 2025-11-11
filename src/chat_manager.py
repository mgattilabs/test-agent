import logging
import uuid
from datetime import datetime

from models import ChatMessage, ChatSession, ChatSessionSummary, MessageRole

logger = logging.getLogger(__name__)


class ChatManager:
    """Manages in-memory chat sessions"""

    def __init__(self):
        self.sessions: dict[str, ChatSession] = {}

    def create_session(self) -> ChatSession:
        """Create a new chat session"""
        chat_id = str(uuid.uuid4())
        session = ChatSession(chat_id=chat_id)
        self.sessions[chat_id] = session
        logger.info(f"Created chat session: {chat_id}")
        return session

    def get_session(self, chat_id: str) -> ChatSession | None:
        """Get a chat session by ID"""
        return self.sessions.get(chat_id)

    def add_message(
        self, chat_id: str, role: MessageRole, content: str
    ) -> ChatMessage | None:
        """Add a message to a chat session"""
        session = self.get_session(chat_id)
        if not session:
            logger.warning(f"Chat session not found: {chat_id}")
            return None

        message = ChatMessage(role=role, content=content)
        session.messages.append(message)
        session.updated_at = datetime.now()
        logger.info(f"Added message to chat {chat_id}: {role.value}")
        return message

    def delete_session(self, chat_id: str) -> bool:
        """Delete a chat session"""
        if chat_id in self.sessions:
            del self.sessions[chat_id]
            logger.info(f"Deleted chat session: {chat_id}")
            return True
        logger.warning(f"Chat session not found for deletion: {chat_id}")
        return False

    def list_sessions(self) -> list[ChatSessionSummary]:
        """List all chat sessions with summary information"""
        summaries = []
        for session in self.sessions.values():
            summary = ChatSessionSummary(
                chat_id=session.chat_id,
                message_count=len(session.messages),
                created_at=session.created_at,
                updated_at=session.updated_at,
                project=session.project,
                pbi_count=len(session.pbis),
                status=session.status,
            )
            summaries.append(summary)
        return summaries

    def get_conversation_history(self, chat_id: str) -> str:
        """Get formatted conversation history for a chat session"""
        session = self.get_session(chat_id)
        if not session:
            return ""

        history_lines = []
        for msg in session.messages:
            history_lines.append(f"{msg.role.value}: {msg.content}")

        return "\n".join(history_lines)

    def update_session_extraction(
        self, chat_id: str, project: str | None, pbis: list
    ) -> bool:
        """Update session with extracted project and PBIs"""
        session = self.get_session(chat_id)
        if not session:
            return False

        session.project = project
        session.pbis = pbis
        session.updated_at = datetime.now()
        logger.info(
            f"Updated chat {chat_id} with project={project} and {len(pbis)} PBIs"
        )
        return True

    def update_session_status(self, chat_id: str, status: str) -> bool:
        """Update the status of a chat session"""
        session = self.get_session(chat_id)
        if not session:
            return False

        session.status = status
        session.updated_at = datetime.now()
        logger.info(f"Updated chat {chat_id} status to: {status}")
        return True
