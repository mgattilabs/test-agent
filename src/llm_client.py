import dspy


class GeminiService:
    lm: dspy.LM

    def __init__(self, api_key: str, model: str = "gemini/gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self._configure_dspy()

    def _configure_dspy(self) -> None:
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY non impostata. Configura la variabile d'ambiente."
            )
        self.lm = dspy.LM(
            self.model,
            api_key=self.api_key,
            cache=False,
            max_tokens=24000,
        )
