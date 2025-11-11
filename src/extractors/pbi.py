import dspy

from src.models import PBI


class ExtractPBIsSignature(dspy.Signature):
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

    summary: str = dspy.InputField(
        desc=(
            "Riassunto della discussione da cui estrarre Product Backlog Items (PBI). "
        )
    )
    pbi_list: list[PBI] = dspy.OutputField(
        desc="Lista di PBI estratti dal sommario. Se il pbi è troppo generico spezzalo in più pbi specifici."
    )


class ExtractPBIModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.program = dspy.ChainOfThought(ExtractPBIsSignature)

    def forward(self, summary: str) -> list[PBI]:
        result = self.program(summary=summary)
        return result.pbi_list
