import dspy


class GeminiService:
    """Service helper to configure DSPy with Gemini."""

    def __init__(self, api_key: str, model: str = "gemini/gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self._configure_dspy()

    def _configure_dspy(self) -> None:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY non impostata. Configura la variabile d'ambiente.")
        lm = dspy.LM(self.model, api_key=self.api_key)
        dspy.configure(lm=lm)
