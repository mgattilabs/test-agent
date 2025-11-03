import dspy

from models import PBI


class ExtractPBIsSignature(dspy.Signature):
    summary: str = dspy.InputField(
        desc=(
            "Riassunto della discussione da cui estrarre Product Backlog Items (PBI). "
        )
    )
    pbi_list: list[PBI] = dspy.OutputField()


class ExtractPBIModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.program = dspy.ChainOfThought(ExtractPBIsSignature)

    def forward(self, summary: str) -> list[PBI]:
        result = self.program(summary=summary)
        return result.pbi_list
