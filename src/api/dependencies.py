"""Dependency injection for API layer.

Following Python philosophy: "Explicit is better than implicit."
All dependencies are clearly defined and injected.
"""

from functools import lru_cache

from config.settings import EnvironmentSettings
from domain.repositories import ChatSessionRepository
from domain.services import (
    AzureDevOpsService,
    PBIExtractionService,
    ProjectExtractionService,
)
from infrastructure.repositories.in_memory_chat_repository import (
    InMemoryChatRepository,
)
from infrastructure.services.azdo_service import AzureDevOpsServiceImpl
from infrastructure.services.dspy_extraction_service import (
    DSPyPBIExtractionService,
    DSPyProjectExtractionService,
)
from llm_client import GeminiService
from use_cases.chat_session_use_cases import (
    AddMessageUseCase,
    ConfirmPBICreationUseCase,
    CreateChatSessionUseCase,
    DeleteChatSessionUseCase,
    GetChatSessionUseCase,
    ListChatSessionsUseCase,
)


@lru_cache
def get_settings() -> EnvironmentSettings:
    """Get application settings (cached singleton)."""
    return EnvironmentSettings()


@lru_cache
def get_repository() -> ChatSessionRepository:
    """Get chat session repository (cached singleton)."""
    return InMemoryChatRepository()


@lru_cache
def get_llm_client():
    """Get LLM client (cached singleton)."""
    settings = get_settings()
    return GeminiService(settings.gemini_api_key)


def get_pbi_extraction_service() -> PBIExtractionService:
    """Get PBI extraction service."""
    return DSPyPBIExtractionService(get_llm_client())


def get_project_extraction_service() -> ProjectExtractionService:
    """Get project extraction service."""
    return DSPyProjectExtractionService(get_llm_client())


def get_azdo_service() -> AzureDevOpsService:
    """Get Azure DevOps service."""
    return AzureDevOpsServiceImpl()


# Use Case Factories
def get_create_session_use_case() -> CreateChatSessionUseCase:
    """Get create session use case."""
    return CreateChatSessionUseCase(repository=get_repository())


def get_add_message_use_case() -> AddMessageUseCase:
    """Get add message use case."""
    return AddMessageUseCase(
        repository=get_repository(),
        pbi_extraction=get_pbi_extraction_service(),
        project_extraction=get_project_extraction_service(),
    )


def get_confirm_pbi_use_case() -> ConfirmPBICreationUseCase:
    """Get confirm PBI creation use case."""
    settings = get_settings()
    return ConfirmPBICreationUseCase(
        repository=get_repository(),
        azdo_service=get_azdo_service(),
        organization=settings.azdo_organization,
    )


def get_get_session_use_case() -> GetChatSessionUseCase:
    """Get session retrieval use case."""
    return GetChatSessionUseCase(repository=get_repository())


def get_list_sessions_use_case() -> ListChatSessionsUseCase:
    """Get list sessions use case."""
    return ListChatSessionsUseCase(repository=get_repository())


def get_delete_session_use_case() -> DeleteChatSessionUseCase:
    """Get delete session use case."""
    return DeleteChatSessionUseCase(repository=get_repository())
