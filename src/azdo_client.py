import logging

from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
from msrest.authentication import BasicAuthentication

from config import settings
from src.models import PBI

logger = logging.getLogger(__name__)

ORGANIZATION_BASE_URL = "https://dev.azure.com/"


def add_pbi(pbis: list[PBI], organization: str, project: str) -> None:
    """Aggiunge una lista di PBI ad Azure DevOps."""

    envs = settings.EnvironmentSettings()
    credentials = BasicAuthentication("", envs.azdo_personal_access_token)
    connection = Connection(
        base_url=f"{ORGANIZATION_BASE_URL}{organization}",
        creds=credentials,
    )

    for pbi in pbis:
        wit_client = connection.clients.get_work_item_tracking_client()
        work_item_data = [
            JsonPatchOperation(op="add", path="/fields/System.Title", value=pbi.title),
            JsonPatchOperation(
                op="add", path="/fields/System.Description", value=pbi.description
            ),
        ]

        wit_client.create_work_item(
            project=project,
            type="Product Backlog Item",
            document=work_item_data,
        )
    logger.info("PBIs processed successfully.")
