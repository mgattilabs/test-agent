from logging import getLogger

import dspy

from config import EnvironmentSettings
from models import Azdo

logger = getLogger(__name__)


class ExtractAzdoSignature(dspy.Signature):
    """
    Sei un assistente esperto di Product Ownership e Agile Project Management.
    Il tuo compito è analizzare un testo in linguaggio naturale (come note, specifiche, richieste di business o verbali di riunione) ed estrarre da esso i Product Backlog Item (PBI) rilevanti.

    Segui con precisione queste regole:

    1. **Identificazione**
    - Individua ogni elemento che rappresenti una funzionalità, un miglioramento, un bug o un requisito tecnico/funzionale.
    - Se un elemento è troppo ampio, complesso o generico (es. "migliorare la gestione utenti"), suddividilo in sotto-PBI specifici e autonomi, ciascuno con un obiettivo chiaro e verificabile.

    2. **Output richiesto**
    Per ogni PBI o sotto-PBI, genera:
    - **titolo** → breve (max 10 parole), chiaro, orientato all’azione, inizia con un verbo (es. “Implementare”, “Aggiungere”, “Ottimizzare”).
    - **descrizione** → spiega il contesto, l’obiettivo e il risultato atteso in 2-4 frasi.

    3. **Tono e stile**
    - Linguaggio professionale, neutro e coerente con le pratiche Agile/Scrum.
    - Evita frasi generiche o ambigue: ogni PBI deve essere **indipendente, chiaro e misurabile**.
    """

    summary: str = dspy.InputField()
    azdo_project: Azdo | None = dspy.OutputField(
        desc="Informazioni di Azure DevOps estratte dal riassunto."
    )


class ExtractAzdoModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.program = dspy.ChainOfThought(ExtractAzdoSignature)

    def forward(self, summary: str) -> Azdo | None:
        result = self.program(summary=summary)
        logger.info(f"Extracted Azure DevOps project: {result.azdo_project}")
        if result.azdo_project is None:
            return None

        return result.azdo_project


if __name__ == "__main__":
    settings = EnvironmentSettings()
    azdo_module = ExtractAzdoModule()
    summary_input = "Project: SampleProject"
    azdo_info = azdo_module.forward(summary=summary_input)
    print(azdo_info)
