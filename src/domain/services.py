"""Service interfaces (ports) for the domain layer."""

from abc import ABC, abstractmethod

from domain.entities import PBI


class PBIExtractionService(ABC):
    """Interface for PBI extraction from text."""

    @abstractmethod
    def extract_pbis(self, conversation: str) -> list[PBI]:
        """Extract PBIs from conversation text."""
        pass


class ProjectExtractionService(ABC):
    """Interface for project extraction from text."""

    @abstractmethod
    def extract_project(self, conversation: str) -> str | None:
        """Extract project name from conversation text."""
        pass


class AzureDevOpsService(ABC):
    """Interface for Azure DevOps operations."""

    @abstractmethod
    def create_pbis(self, pbis: list[PBI], organization: str, project: str) -> None:
        """Create PBIs in Azure DevOps."""
        pass
