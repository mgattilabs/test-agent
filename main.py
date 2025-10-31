from pprint import pprint

import dspy

from config import EnvironmentSettings
from gemini_service import GeminiService
from models import PBI, ActionResponse, AgentResponse, Azdo


class ExtractPBIsSignature(dspy.Signature):
    summary: str = dspy.InputField(
        desc=(
            "Riassunto della discussione da cui estrarre Product Backlog Items (PBI). "
        )
    )
    pbi_list: list[PBI] = dspy.OutputField(
        desc="Elenco dei Product Backlog Items (PBI) estratti dal riassunto."
    )


class ExtractPBIModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.program = dspy.ChainOfThought(ExtractPBIsSignature)

    def forward(self, summary: str) -> list[PBI]:
        result = self.program(summary=summary)
        return result.pbi_list


class PbiAgent:
    def __init__(self, settings: EnvironmentSettings):
        self.gemini = GeminiService(settings.gemini_api_key)
        self.extract_pbi_module = ExtractPBIModule()

    def process_flow(self, summary: str) -> AgentResponse:
        pbi_list = self.extract_pbi_module(summary=summary)

        if pbi_list:
            return AgentResponse(
                action=ActionResponse.create_pbi_list(), pbi_list=pbi_list
            )
        return AgentResponse()


class ExtractAzdoSignature(dspy.Signature):
    summary: str = dspy.InputField()
    azdo_info: Azdo = dspy.OutputField(
        desc="Informazioni di Azure DevOps estratte dal riassunto."
    )


class ExtractAzdoModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.program = dspy.ChainOfThought(ExtractAzdoSignature)

    def forward(self, summary: str) -> Azdo:
        result = self.program(summary=summary)
        return result


class AzdoAgent:
    def __init__(self, settings: EnvironmentSettings):
        self.gemini = GeminiService(settings.gemini_api_key)
        self.extract_azdo_module = ExtractAzdoModule()

    def process_flow(self, summary: str) -> Azdo:
        result = self.extract_azdo_module(summary=summary)
        return result


if __name__ == "__main__":
    settings = EnvironmentSettings()
    pbi_agent = PbiAgent(settings)
    azdo_agent = AzdoAgent(settings)

    test_summary = """
        crea un elenco di Product Backlog Items (PBI) sulla progetto francigena di engage labs basati sul seguente riassunto della discussione:
        Il sistema di gestione dei progetti deve consentire agli utenti di creare, modificare e
        eliminare attività. Ogni attività deve avere un titolo, una descrizione, una data di scadenza
        e uno stato (ad esempio, "In corso", "Completato", "In sospeso"). Gli utenti devono essere
        in grado di assegnare priorità alle attività e di visualizzarle in base alla priorità o alla
        data di scadenza. Inoltre, il sistema deve inviare notifiche via email agli utenti quando
        una attività sta per scadere o è stata completata.
        Aggiungi anche la gestione dell'autenticazione degli utenti e dei ruoli.
    """

    # result = agent.process_flow(test_summary)

    # pprint(result, indent=4)

    response = azdo_agent.process_flow(summary=test_summary)
    pprint(response, indent=4)
