from pydantic import BaseModel


class PBI(BaseModel):
    title: str
    description: str


class AgentResponse(BaseModel):
    action: str | None = None
    pbi_list: list[PBI] | None = None


class Azdo(BaseModel):
    organization: str
    project: str


class ActionResponse:
    @staticmethod
    def create_pbi_list() -> str:
        return "create_pbi_list"
