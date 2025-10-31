from pydantic_settings import BaseSettings


class EnvironmentSettings(BaseSettings):
    gemini_api_key: str
    azdo_personal_access_token: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
