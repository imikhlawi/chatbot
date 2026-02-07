from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "pdf-chatbot-api"
    ENV: str = "local"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    LLM_BASE_URL: str = "http://127.0.0.1:8080"
    LLM_TIMEOUT_SECONDS: int = 300

    CORS_ORIGINS: str = "http://localhost:3000"

    def cors_origins_list(self) -> List[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]


settings = Settings()
