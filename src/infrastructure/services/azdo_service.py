"""Azure DevOps service implementation."""

import logging

from domain.entities import PBI
from domain.services import AzureDevOpsService
import azdo_client as legacy_azdo_client

logger = logging.getLogger(__name__)


class AzureDevOpsServiceImpl(AzureDevOpsService):
    """Azure DevOps operations implementation."""

    def create_pbis(self, pbis: list[PBI], organization: str, project: str) -> None:
        """Create PBIs in Azure DevOps."""
        # Convert domain PBIs to the format expected by legacy client
        from models import PBI as LegacyPBI

        legacy_pbis = [
            LegacyPBI(title=pbi.title, description=pbi.description) for pbi in pbis
        ]

        try:
            legacy_azdo_client.add_pbi(
                pbis=legacy_pbis, organization=organization, project=project
            )
            logger.info(f"Created {len(pbis)} PBIs in project {project}")
        except Exception as e:
            logger.error(f"Error creating PBIs in Azure DevOps: {e}", exc_info=True)
            raise
