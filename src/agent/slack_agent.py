import json
import dspy
from src.services.gemini_service import GeminiService


class ExtractPBIsSignature(dspy.Signature):
    summary = dspy.InputField(
        desc=(
            "Riassunto della discussione da cui estrarre Product Backlog Items (PBI). "
            "Sii permissivo: anche se mancano dettagli, crea comunque PBI come traccia sul lavoro da svolgere."
        )
    )
    pbi_list = dspy.OutputField(
        desc=(
            "JSON array di PBI. Ogni elemento ha formato {\"title\": \"titolo breve del PBI\", \"description\": \"descrizione dettagliata dell'attività\"}. "
            "Crea sempre almeno un PBI se possibile, anche con informazioni parziali. "
            "Chiedi chiarimenti solo se il riassunto è completamente vuoto o incomprensibile."
        )
    )
    clarifying_questions = dspy.OutputField(
        desc=(
            "JSON array di domande di chiarimento. "
            "Usa [] (array vuoto) se riesci a creare almeno un PBI. "
            "Chiedi solo se il riassunto è davvero troppo vago o incomprensibile."
        )
    )


class ExtractPBIModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.program = dspy.ChainOfThought(ExtractPBIsSignature)

    def forward(self, summary: str):
        result = self.program(summary=summary)
        pbi_list = self._parse_json(result.pbi_list, default=[], wrap_on_fail=False)
        questions = self._parse_json(result.clarifying_questions, default=[], wrap_on_fail=True)
        return pbi_list, questions

    @staticmethod
    def _parse_json(payload: str, default, wrap_on_fail: bool):
        if not payload:
            return default
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return [payload.strip()] if wrap_on_fail and payload.strip() else default


class SlackAgent:
    def __init__(self, settings):
        self.gemini = GeminiService(settings.gemini_api_key)
        self.extract_pbi_module = ExtractPBIModule()

    def process_flow(self, summary: str):
        pbi_list, questions = self.extract_pbi_module(summary)
        
        # Se ci sono PBI generati, restituiscili (anche se ci sono domande)
        if pbi_list:
            return {"action": "create_pbi_list", "pbi_list": pbi_list}
        
        # Altrimenti, se ci sono domande, richiedile
        if questions:
            return {"action": "ask_for_info", "questions": questions}
        
        # Caso estremo: né PBI né domande
        return {
            "action": "ask_for_info",
            "questions": ["Il riassunto fornito non è sufficientemente chiaro. Puoi fornire maggiori dettagli?"]
        }
