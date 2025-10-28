from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Gestisce la configurazione dell'applicazione."""

    gemini_api_key: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
