from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class EnvironmentSettings(BaseSettings):
    gemini_api_key: str
    azdo_personal_access_token: str
    azdo_organization: str

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")
