from logging import getLogger

import dspy

from config import EnvironmentSettings
from models import Azdo

logger = getLogger(__name__)


class ExtractAzdoSignature(dspy.Signature):
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
