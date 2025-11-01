from logging import basicConfig, getLogger

import dspy
from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
from msrest.authentication import BasicAuthentication

from azdo_agent import ExtractAzdoModule
from config import EnvironmentSettings
from gemini_service import GeminiService
from models import PBI, Azdo
from pbi_processor import ExtractPBIModule

basicConfig(level="INFO")
logger = getLogger(__name__)

ORGANIZATION_BASE_URL = "https://dev.azure.com/"


class AzdoAgent:
    def __init__(self):
        self.azdo_project: Azdo = None
        self.pbis: list[PBI] = []
        self.azdo_module = ExtractAzdoModule()
        self.pbi_module = ExtractPBIModule()

    def process_flow(self, summary: str) -> None:
        self.azdo_project = self.azdo_module(summary=summary)
        self.pbis = self.pbi_module(summary=summary)

    def process_pbi(self, summary: str):
        self.pbis = self.pbiModule(summary=summary)

    def process_azdo(self, summary: str):
        self.azdo_project = self.azdoModule(summary=summary)



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
    wit_client = connection.clients.get_work_item_tracking_client()
    for pbi in azdo_agent.pbis:
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
    dspy.configure(lm=GeminiService(api_key=settings.gemini_api_key).lm)

    azdo_agent = AzdoAgent()
    credentials = BasicAuthentication("", settings.azdo_personal_access_token)

    while True:
        print("Inserisci il sommario per estrarre i pbi e i dettagli di Azure DevOps:")
        summary = input()
        azdo_agent.process_flow(summary=summary)

        if len(azdo_agent.pbis) == 0:
            print("Nessun PBI estratto. Inserisci il sommario dei PBI:")
            summary_pbi = input()
            azdo_agent.process_pbi(summary=summary_pbi)

        if azdo_agent.azdo_project is None:
            print("inserisci progetto di Azure DevOps")
            summary_azdo = input()
            azdo_agent.process_azdo(summary=summary_azdo)

        process_backlog_items(
            logger, settings.azdo_organization, azdo_agent, credentials
        )

        exit_input = input(
            "Vuoi uscire? (scrivi 'exit' per uscire, premi invio per continuare): "
        )
        if exit_input.lower() == "exit":
            break
