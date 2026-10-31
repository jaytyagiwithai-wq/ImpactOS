from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from functools import lru_cache
from pathlib import Path
from pydantic import SecretStr
BACKEND_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "ImpactOS API"
    app_env: Literal["local","test","staging","production"] = "local"
    debug: bool = False
    database_url: SecretStr
    openai_api_key: SecretStr
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    embedding_batch_size: int = 100

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="IMPACTOS_",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
