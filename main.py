#!/usr/bin/env python3
"""FastMCP 2.0 server che espone AzdoProjectHandler come tool."""

from logging import basicConfig, getLogger

import dspy
from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
from msrest.authentication import BasicAuthentication

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise ImportError(
        "FastMCP non è installato. Installa con: pip install mcp"
    ) from exc

from azdo_module import ExtractAzdoModule
from config import EnvironmentSettings
from gemini_service import GeminiService
from models import PBI, Azdo
from pbi_module import ExtractPBIModule

basicConfig(level="INFO")
logger = getLogger(__name__)

ORGANIZATION_BASE_URL = "https://dev.azure.com/"

# Inizializza il server FastMCP
mcp = FastMCP("azdo-handler")


class AzdoProjectHandler:
    """Handler per elaborare PBIs e progetti Azure DevOps."""

    def __init__(self):
        self.azdo_project: Azdo | None = None
        self.pbis: list[PBI] = []
        self.azdo_module = ExtractAzdoModule()
        self.pbi_module = ExtractPBIModule()

    def process_flow(self, summary: str) -> None:
        """Elabora sommario completo per estrarre progetto e PBIs."""
        self.azdo_project = self.azdo_module(summary=summary)  # type: ignore[assignment]
        self.pbis = self.pbi_module(summary=summary)  # type: ignore[assignment]

    def process_pbi(self, summary: str):
        """Elabora solo i PBIs."""
        self.pbis = self.pbi_module(summary=summary)  # type: ignore[assignment]

    def process_azdo(self, summary: str):
        """Elabora solo il progetto Azure DevOps."""
        self.azdo_project = self.azdo_module(summary=summary)  # type: ignore[assignment]


def process_backlog_items(logger, organization, azdo_agent, credentials):
    connection = Connection(
        base_url=f"{ORGANIZATION_BASE_URL}{organization}",
        creds=credentials,
    )

    if len(azdo_agent.pbis) == 0:
        logger.info("No PBIs to process.")
        return

    for pbi in azdo_agent.pbis:
        wit_client = connection.clients.get_work_item_tracking_client()
        work_item_data = [
            JsonPatchOperation(op="add", path="/fields/System.Title", value=pbi.title),
            JsonPatchOperation(
                op="add", path="/fields/System.Description", value=pbi.description
            ),
        ]

        wit_client.create_work_item(
            project=azdo_agent.azdo_project.project,
            type="Product Backlog Item",
            document=work_item_data,
        )
    logger.info("PBIs processed successfully.")


# Stato globale del server
_handler: AzdoProjectHandler | None = None
_settings: EnvironmentSettings | None = None
_credentials: BasicAuthentication | None = None


def _ensure_initialized() -> bool:
    """Verifica che il sistema sia stato inizializzato."""
    return all([_handler is not None, _settings is not None, _credentials is not None])


@mcp.tool()
async def initialize_azdo_handler() -> dict:
    """
    Inizializza il sistema AzdoProjectHandler.

    Configura DSPy con Gemini, prepara le credenziali Azure DevOps
    e crea un'istanza del handler.

    Returns:
        dict: Risultato dell'inizializzazione con success (bool) e message (str)
    """
    global _handler, _settings, _credentials

    try:
        _settings = EnvironmentSettings()  # type: ignore[call-arg]
        dspy.configure(lm=GeminiService(api_key=_settings.gemini_api_key).lm)
        _handler = AzdoProjectHandler()
        _credentials = BasicAuthentication("", _settings.azdo_personal_access_token)

        logger.info("Sistema inizializzato correttamente")
        return {
            "success": True,
            "message": "Sistema inizializzato correttamente",
            "organization": _settings.azdo_organization,
        }
    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione: {e}")
        return {"success": False, "message": f"Errore di inizializzazione: {str(e)}"}


@mcp.tool()
async def process_azdo_summary(summary: str) -> dict:
    """
    Elabora un sommario per estrarre PBIs e progetto Azure DevOps.

    Args:
        summary: Testo del sommario da elaborare

    Returns:
        dict: Contiene success, message, pbis_count, pbis (list) e azdo_project (dict)
    """
    if not _ensure_initialized():
        return {
            "success": False,
            "message": "Sistema non inizializzato. Chiamare prima initialize_azdo_handler",
        }

    try:
        assert _handler is not None
        _handler.process_flow(summary=summary)

        pbis_data = [
            {"title": pbi.title, "description": pbi.description}
            for pbi in _handler.pbis
        ]

        project_data = (
            {"project": _handler.azdo_project.project}
            if _handler.azdo_project
            else None
        )

        logger.info(f"Elaborati {len(pbis_data)} PBIs")
        return {
            "success": True,
            "message": "Elaborazione completata",
            "pbis_count": len(pbis_data),
            "pbis": pbis_data,
            "azdo_project": project_data,
        }
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione: {e}")
        return {"success": False, "message": f"Errore di elaborazione: {str(e)}"}


@mcp.tool()
async def extract_pbis_only(summary: str) -> dict:
    """
    Estrae solo i PBIs da un sommario.

    Args:
        summary: Testo del sommario da cui estrarre i PBIs

    Returns:
        dict: Contiene success, message, pbis_count e pbis (list)
    """
    if not _ensure_initialized():
        return {
            "success": False,
            "message": "Sistema non inizializzato. Chiamare prima initialize_azdo_handler",
        }

    try:
        assert _handler is not None
        _handler.process_pbi(summary=summary)

        pbis_data = [
            {"title": pbi.title, "description": pbi.description}
            for pbi in _handler.pbis
        ]

        logger.info(f"Estratti {len(pbis_data)} PBIs")
        return {
            "success": True,
            "message": "PBIs estratti con successo",
            "pbis_count": len(pbis_data),
            "pbis": pbis_data,
        }
    except Exception as e:
        logger.error(f"Errore durante l'estrazione dei PBIs: {e}")
        return {"success": False, "message": f"Errore estrazione PBIs: {str(e)}"}


@mcp.tool()
async def extract_azdo_project_only(summary: str) -> dict:
    """
    Estrae solo il progetto Azure DevOps da un sommario.

    Args:
        summary: Testo del sommario da cui estrarre il progetto

    Returns:
        dict: Contiene success, message e azdo_project (dict)
    """
    if not _ensure_initialized():
        return {
            "success": False,
            "message": "Sistema non inizializzato. Chiamare prima initialize_azdo_handler",
        }

    try:
        assert _handler is not None
        _handler.process_azdo(summary=summary)

        project_data = (
            {"project": _handler.azdo_project.project}
            if _handler.azdo_project
            else None
        )

        logger.info("Progetto Azure DevOps estratto")
        return {
            "success": True,
            "message": "Progetto Azure DevOps estratto",
            "azdo_project": project_data,
        }
    except Exception as e:
        logger.error(f"Errore durante l'estrazione del progetto: {e}")
        return {"success": False, "message": f"Errore estrazione progetto: {str(e)}"}


@mcp.tool()
async def submit_pbis_to_azdo() -> dict:
    """
    Invia i PBIs correnti al backlog di Azure DevOps.

    Returns:
        dict: Contiene success e message con il numero di PBIs inviati
    """
    if not _ensure_initialized():
        return {
            "success": False,
            "message": "Sistema non inizializzato. Chiamare prima initialize_azdo_handler",
        }

    try:
        assert _handler is not None
        assert _settings is not None
        assert _credentials is not None

        if not _handler.pbis:
            return {"success": False, "message": "Nessun PBI disponibile per l'invio"}

        if _handler.azdo_project is None:
            return {
                "success": False,
                "message": "Nessun progetto Azure DevOps configurato",
            }

        process_backlog_items(
            logger, _settings.azdo_organization, _handler, _credentials
        )

        count = len(_handler.pbis)
        logger.info(f"Inviati {count} PBIs ad Azure DevOps")
        return {
            "success": True,
            "message": f"Inviati {count} PBIs ad Azure DevOps con successo",
        }
    except Exception as e:
        logger.error(f"Errore durante l'invio dei PBIs: {e}")
        return {"success": False, "message": f"Errore invio PBIs: {str(e)}"}


@mcp.tool()
async def get_handler_state() -> dict:
    """
    Ottiene lo stato corrente del handler (PBIs e progetto caricati).

    Returns:
        dict: Contiene success, pbis_count, pbis (list) e azdo_project (dict)
    """
    if not _ensure_initialized():
        return {
            "success": False,
            "message": "Sistema non inizializzato. Chiamare prima initialize_azdo_handler",
        }

    assert _handler is not None

    pbis_data = [
        {"title": pbi.title, "description": pbi.description} for pbi in _handler.pbis
    ]

    project_data = (
        {"project": _handler.azdo_project.project} if _handler.azdo_project else None
    )

    return {
        "success": True,
        "pbis_count": len(pbis_data),
        "pbis": pbis_data,
        "azdo_project": project_data,
    }


@mcp.tool()
async def reset_handler() -> dict:
    """
    Reimposta il handler creando una nuova istanza vuota.

    Returns:
        dict: Contiene success e message
    """
    if not _ensure_initialized():
        return {
            "success": False,
            "message": "Sistema non inizializzato. Chiamare prima initialize_azdo_handler",
        }

    global _handler

    try:
        _handler = AzdoProjectHandler()
        logger.info("Handler reimpostato")
        return {"success": True, "message": "Handler reimpostato con successo"}
    except Exception as e:
        logger.error(f"Errore durante il reset: {e}")
        return {"success": False, "message": f"Errore reset: {str(e)}"}


def main():
    """Avvia il server FastMCP in modalità stdio."""
    logger.info("Avvio server FastMCP azdo-handler...")
    mcp.run(transport="http", host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
