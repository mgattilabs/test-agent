"""Use cases for chat session management."""

import logging
from dataclasses import dataclass
from uuid import UUID

from domain.entities import ChatSession, MessageRole, SessionStatus
from domain.repositories import ChatSessionRepository
from domain.services import (
    AzureDevOpsService,
    PBIExtractionService,
    ProjectExtractionService,
)

logger = logging.getLogger(__name__)


@dataclass
class CreateChatSessionUseCase:
    """Create a new chat session."""

    repository: ChatSessionRepository

    def execute(self) -> ChatSession:
        """Execute the use case."""
        session = ChatSession()
        self.repository.save(session)
        logger.info(f"Created chat session: {session.chat_id}")
        return session


@dataclass
class AddMessageUseCase:
    """Add a message to a chat session."""

    repository: ChatSessionRepository
    pbi_extraction: PBIExtractionService
    project_extraction: ProjectExtractionService

    def execute(
        self, chat_id: UUID, role: MessageRole, content: str
    ) -> tuple[ChatSession, str | None]:
        """
        Execute the use case.

        Returns:
            tuple: (updated_session, assistant_response)
        """
        session = self.repository.get_by_id(chat_id)
        if not session:
            raise ValueError(f"Chat session not found: {chat_id}")

        # Add the message
        session.add_message(role, content)
        self.repository.save(session)

        # If it's a user message, analyze and generate assistant response
        if role == MessageRole.USER:
            assistant_response = self._analyze_and_respond(session)

            # Add assistant response to session
            if assistant_response:
                session.add_message(MessageRole.ASSISTANT, assistant_response)
                self.repository.save(session)

            return session, assistant_response

        return session, None

    def _analyze_and_respond(self, session: ChatSession) -> str:
        """Analyze session and generate appropriate response."""
        if not session.is_ready_for_extraction():
            return "Come posso aiutarti con l'estrazione di PBI?"

        conversation = session.get_conversation_history()

        # Extract information
        project = self.project_extraction.extract_project(conversation)
        pbis = self.pbi_extraction.extract_pbis(conversation)

        # Update session
        session.update_extraction(project, pbis)

        # Determine response based on what's missing
        if session.needs_project_info():
            session.update_status(SessionStatus.NEEDS_INFO)
            return "Non ho identificato il progetto Azure DevOps. Puoi specificare il nome del progetto?"

        if session.needs_requirements():
            session.update_status(SessionStatus.NEEDS_INFO)
            return f"Ho identificato il progetto '{project}', ma non ho ancora informazioni sufficienti per creare PBI. Puoi descrivere le funzionalità o i requisiti che vuoi implementare?"

        # All info present - ready for confirmation
        session.update_status(SessionStatus.READY_FOR_CONFIRMATION)
        session.awaiting_confirmation = True

        pbi_summary = "\n".join(
            f"{i + 1}. {pbi.title}" for i, pbi in enumerate(session.pbis)
        )

        return f"Perfetto! Ho identificato il progetto '{project}' e ho estratto {len(session.pbis)} PBI:\n\n{pbi_summary}\n\nVuoi che proceda con la creazione di questi PBI in Azure DevOps? (Usa l'endpoint /chat/sessions/{session.chat_id}/confirm per confermare)"


@dataclass
class ConfirmPBICreationUseCase:
    """Confirm and create PBIs in Azure DevOps."""

    repository: ChatSessionRepository
    azdo_service: AzureDevOpsService
    organization: str

    def execute(self, chat_id: UUID, confirmed: bool) -> tuple[bool, str]:
        """
        Execute the use case.

        Returns:
            tuple: (success, message)
        """
        session = self.repository.get_by_id(chat_id)
        if not session:
            raise ValueError(f"Chat session not found: {chat_id}")

        if not session.awaiting_confirmation:
            raise ValueError(
                "This session is not awaiting confirmation. Add messages with requirements first."
            )

        if not confirmed:
            # User rejected - reset status
            session.update_status(SessionStatus.ACTIVE)
            session.awaiting_confirmation = False
            session.add_message(
                MessageRole.ASSISTANT,
                "Ok, nessun problema. Puoi modificare o aggiungere ulteriori requisiti.",
            )
            self.repository.save(session)
            return (
                True,
                "Creazione PBI annullata. Puoi continuare a modificare i requisiti.",
            )

        # User confirmed - create PBIs
        if not session.is_complete():
            raise ValueError("Missing information. Project or PBIs not identified.")

        try:
            self.azdo_service.create_pbis(
                session.pbis, self.organization, session.project
            )

            session.update_status(SessionStatus.COMPLETED)
            session.awaiting_confirmation = False
            session.add_message(
                MessageRole.ASSISTANT,
                f"Perfetto! Ho creato {len(session.pbis)} PBI nel progetto '{session.project}' in Azure DevOps.",
            )
            self.repository.save(session)

            logger.info(
                f"Successfully created {len(session.pbis)} PBIs for chat {chat_id}"
            )

            return (
                True,
                f"Creati con successo {len(session.pbis)} PBI nel progetto '{session.project}'.",
            )

        except Exception as e:
            logger.error(f"Error creating PBIs: {e}", exc_info=True)
            session.update_status(SessionStatus.ERROR)
            session.add_message(
                MessageRole.ASSISTANT,
                "Si è verificato un errore durante la creazione dei PBI. Riprova più tardi.",
            )
            self.repository.save(session)
            raise


@dataclass
class GetChatSessionUseCase:
    """Retrieve a chat session."""

    repository: ChatSessionRepository

    def execute(self, chat_id: UUID) -> ChatSession | None:
        """Execute the use case."""
        return self.repository.get_by_id(chat_id)


@dataclass
class ListChatSessionsUseCase:
    """List all chat sessions."""

    repository: ChatSessionRepository

    def execute(self) -> list[ChatSession]:
        """Execute the use case."""
        return self.repository.get_all()


@dataclass
class DeleteChatSessionUseCase:
    """Delete a chat session."""

    repository: ChatSessionRepository

    def execute(self, chat_id: UUID) -> bool:
        """Execute the use case."""
        return self.repository.delete(chat_id)
