import logging
import uuid
from datetime import datetime

from fastmcp import FastMCP

from extractors.pbi import ExtractPBIModule
from models import PBI
from src import azdo_client, llm_client
from src.config import settings
from src.extractors.azdo import ExtractAzdoModule

logger = logging.getLogger(__name__)

mcp = FastMCP("Engage Azdo Agent")

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


def _format_pbis_as_table(pbis: list[PBI]) -> str:
    if not pbis:
        return "Nessun PBI estratto."

    # Header della tabella
    table = "| # | Title | Description |\n"
    table += "|---|-------|-------------|\n"

    for i, pbi in enumerate(pbis, 1):
        title = pbi.title.replace("|", "\\|")
        description = pbi.description.replace("|", "\\|")
        table += f"| {i} | {title} | {description} |\n"

    return table


@mcp.tool()
def process_azdo_summary(summary: str) -> str:
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
    except Exception as e:
        logger.error(
            f"[{request_id}] Errore durante l'estrazione dei PBI: {e}", exc_info=True
        )
        _log_request(request_id, summary, None, [], "error")
        raise e


@mcp.tool()
def save_pbis_to_azdo() -> None:
    envSettings = settings.EnvironmentSettings()

    try:
        logger.info(f"Saved {len(pbis)} PBIs to Azure DevOps project '{project}'")
    except Exception as e:
        logger.error(f"Failed to save PBIs to Azure DevOps: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("Starting MCP server...")

    mcp.run()
