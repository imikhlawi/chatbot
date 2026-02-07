from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "pdf-chatbot-api"
    ENV: str = "local"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    LLM_BASE_URL: str = "http://127.0.0.1:8080"
    LLM_TIMEOUT_SECONDS: int = 300

    CORS_ORIGINS: str = "http://localhost:3000"

    # Chroma (Docker: chroma:8000, lokal: 127.0.0.1:8001)
    CHROMA_HOST: str = "127.0.0.1"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION: str = "pdf_chatbot"

    # RAG
    RAG_TOP_K: int = 4
    RAG_MAX_CONTEXT_CHARS: int = 12000
    RAG_MAX_CHUNKS_PER_INGEST: int = 2000
    MAX_UPLOAD_MB: int = 50

    # Optional: wenn gesetzt, wird X-API-Key Header verlangt
    API_KEY: Optional[str] = None

    def cors_origins_list(self) -> List[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]


settings = Settings()


def get_settings() -> Settings:
    """Für Dependency Injection oder direkten Zugriff (z. B. in deps-Router)."""
    return settings
