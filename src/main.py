from fastapi import FastAPI
from pydantic import BaseModel

from src.agent.slack_agent import SlackAgent
from src.config.settings import Settings


app = FastAPI()
settings = Settings()
agent = SlackAgent(settings)

app = FastAPI()
settings = Settings()
agent = SlackAgent(settings)

class DiscussionRequest(BaseModel):
    summary: str

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.post("/discussion")
def receive_discussion(request: DiscussionRequest):
    summary = request.summary
    return agent.process_flow(summary)
