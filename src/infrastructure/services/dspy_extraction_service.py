"""DSPy-based extraction service implementations."""

import logging

from src.domain.entities import PBI
from src.domain.services import PBIExtractionService, ProjectExtractionService
from src.extractors import ExtractPBIModule
from src.extractors.azdo import ExtractAzdoModule

logger = logging.getLogger(__name__)


class DSPyPBIExtractionService(PBIExtractionService):
    """PBI extraction using DSPy."""

    def __init__(self, llm_client):
        self._llm_client = llm_client
        self._extractor = ExtractPBIModule()
        self._extractor.set_lm(llm_client.lm)

    def extract_pbis(self, conversation: str) -> list[PBI]:
        """Extract PBIs from conversation text."""
        try:
            result = self._extractor(summary=conversation)
            # Convert from Pydantic models to domain entities
            return [PBI(title=pbi.title, description=pbi.description) for pbi in result]
        except Exception as e:
            logger.error(f"Error extracting PBIs: {e}", exc_info=True)
            return []


class DSPyProjectExtractionService(ProjectExtractionService):
    """Project extraction using DSPy."""

    def __init__(self, llm_client):
        self._llm_client = llm_client
        self._extractor = ExtractAzdoModule()
        self._extractor.set_lm(llm_client.lm)

    def extract_project(self, conversation: str) -> str | None:
        """Extract project name from conversation text."""
        try:
            result = self._extractor(summary=conversation)
            return result if result else None
        except Exception as e:
            logger.error(f"Error extracting project: {e}", exc_info=True)
            return None
