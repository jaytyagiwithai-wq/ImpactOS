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
    retrieval_candidate_limit: int = 30
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    reranker_batch_size: int = 16
    reranker_max_length: int = 512
    reranker_candidate_limit: int = 20

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="IMPACTOS_",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
