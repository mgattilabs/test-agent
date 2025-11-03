from logging import basicConfig, getLogger

import dspy
from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
from msrest.authentication import BasicAuthentication

from azdo_module import ExtractAzdoModule
from config import EnvironmentSettings
from gemini_service import GeminiService
from models import PBI, Azdo
from pbi_module import ExtractPBIModule

basicConfig(level="INFO")
logger = getLogger(__name__)

ORGANIZATION_BASE_URL = "https://dev.azure.com/"


class AzdoProjectHandler:
    def __init__(self):
        self.azdo_project: Azdo = None
        self.pbis: list[PBI] = []
        self.azdo_module = ExtractAzdoModule()
        self.pbi_module = ExtractPBIModule()

    def process_flow(self, summary: str) -> None:
        self.azdo_project = self.azdo_module(summary=summary)
        self.pbis = self.pbi_module(summary=summary)

    def process_pbi(self, summary: str):
        self.pbis = self.pbi_module(summary=summary)

    def process_azdo(self, summary: str):
        self.azdo_project = self.azdo_module(summary=summary)


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


def get_non_empty_input(prompt: str, max_retries: int = 3) -> str | None:
    for attempt in range(max_retries):
        try:
            user_input = input(prompt).strip()
            if user_input:
                return user_input
            remaining = max_retries - attempt - 1
            if remaining > 0:
                print(f"Input non valido. Riprova ({remaining} tentativi rimasti).")
            else:
                print("Troppi tentativi falliti.")
                return None
        except KeyboardInterrupt:
            print("\nOperazione annullata dall'utente.")
            return None
        except Exception as e:
            logger.error(f"Errore durante l'input: {e}")
            print(f"Errore durante l'input: {e}")
            return None
    return None


if __name__ == "__main__":
    try:
        settings = EnvironmentSettings()
        dspy.configure(lm=GeminiService(api_key=settings.gemini_api_key).lm)
    except Exception as e:
        logger.error(f"Errore nella configurazione iniziale: {e}")
        print(f"Errore nella configurazione: {e}")
        exit(1)

    azdo_agent = AzdoProjectHandler()
    credentials = BasicAuthentication("", settings.azdo_personal_access_token)

    while True:
        try:
            summary = get_non_empty_input(
                "Inserisci il sommario per estrarre i PBI e i dettagli di Azure DevOps:\n> "
            )
            if summary is None:
                continue

            try:
                azdo_agent.process_flow(summary=summary)
                logger.info("Elaborazione iniziale completata.")
            except Exception as e:
                logger.error(f"Errore nell'elaborazione del flusso: {e}")
                print(f"Errore nell'elaborazione: {e}")
                print("Riprovare con un altro sommario.")
                continue

            if len(azdo_agent.pbis) == 0:
                print("Nessun PBI estratto.")
                summary_pbi = get_non_empty_input("Inserisci il sommario dei PBI:\n> ")
                if summary_pbi is not None:
                    try:
                        azdo_agent.process_pbi(summary=summary_pbi)
                        logger.info("Elaborazione PBI completata.")
                    except Exception as e:
                        logger.error(f"Errore nell'estrazione dei PBI: {e}")
                        print(f"Errore nell'estrazione dei PBI: {e}")
                        continue

            if azdo_agent.azdo_project is None:
                summary_azdo = get_non_empty_input(
                    "Inserisci il progetto di Azure DevOps:\n> "
                )
                if summary_azdo is not None:
                    try:
                        azdo_agent.process_azdo(summary=summary_azdo)
                        logger.info("Elaborazione progetto Azure DevOps completata.")
                    except Exception as e:
                        logger.error(f"Errore nell'estrazione del progetto: {e}")
                        print(f"Errore nell'estrazione del progetto: {e}")
                        continue

            if len(azdo_agent.pbis) == 0:
                print("Impossibile continuare: nessun PBI disponibile.")
                continue

            if azdo_agent.azdo_project is None:
                print(
                    "Impossibile continuare: nessun progetto Azure DevOps disponibile."
                )
                continue

            try:
                process_backlog_items(
                    logger, settings.azdo_organization, azdo_agent, credentials
                )
            except Exception as e:
                logger.error(f"Errore nell'elaborazione dei backlog items: {e}")
                print(f"Errore nell'elaborazione dei backlog items: {e}")
                continue

            exit_input = get_non_empty_input(
                "Vuoi uscire? (scrivi 'exit' per uscire, premi invio per continuare):\n> "
            )
            if exit_input and exit_input.lower() == "exit":
                logger.info("Applicazione terminata dall'utente.")
                print("Arrivederci!")
                break

        except KeyboardInterrupt:
            print("\nApplicazione interrotta.")
            logger.info("Applicazione interrotta dall'utente.")
            break
        except Exception as e:
            logger.error(f"Errore inaspettato nel ciclo principale: {e}")
            print(f"Errore inaspettato: {e}")
            print("Riprova da capo.")
