import http

from fastapi import FastAPI
from pydantic import BaseModel

import azdo_client
from config.settings import EnvironmentSettings
from extractors import ExtractPBIModule
from llm_client import GeminiService

app = FastAPI()
env = EnvironmentSettings()
gemini_service = GeminiService(env.gemini_api_key)


class PbiRequest(BaseModel):
    summary: str


class MessageResponse(BaseModel):
    message: str


@app.post("/pbi-creator")
async def pbi_creator(
    request: PbiRequest, status_code=http.HTTPStatus.OK
) -> MessageResponse:
    extractor = ExtractPBIModule()
    extractor.set_lm(gemini_service.lm)

    response = extractor(request.summary)

    if len(response.pbis) == 0:
        return MessageResponse(message="No PBIs extracted from the input.")

    if "project" not in response:
        return MessageResponse(
            message="Project information is missing in the response."
        )

    for pbi in response.pbis:
        azdo_client.add_pbi(
            pbis=response.pbis,
            organization=env.azdo_organization,
            project=response.project,
        )

    return MessageResponse(message="PBIs created successfully.")
