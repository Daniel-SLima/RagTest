from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RagTest API"
    app_version: str = "0.5.13"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str | None = None
    qdrant_timeout_seconds: int = 10
    qdrant_collection: str = "ragtest_documents"

    source_dir: Path = Path("data/source")
    chunk_size: int = 1000
    chunk_overlap: int = 200

    pdf_ocr_enabled: bool = True
    pdf_ocr_language: str = "por"
    pdf_ocr_dpi: int = 200
    pdf_ocr_timeout_seconds: int = 60

    embedding_provider: str = "fastembed"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_batch_size: int = 32
    embedding_cache_dir: Path = Path(".cache/fastembed")
    upsert_batch_size: int = 64

    sparse_embedding_provider: str = "fastembed_bm25"
    sparse_embedding_model: str = "Qdrant/bm25"
    sparse_embedding_language: str = "portuguese"

    retrieval_mode: Literal["dense", "dense-rerank", "hybrid"] = "dense-rerank"
    retrieval_merge_same_page: bool = True
    retrieval_max_group_chars: int = 5000
    retrieval_auto_decompose: bool = True
    retrieval_max_subqueries: int = Field(default=3, ge=2, le=4)

    llm_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    llm_temperature: float = 0.1
    llm_max_output_tokens: int = 2400

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("qdrant_api_key", "gemini_api_key", mode="before")
    @classmethod
    def empty_secret_is_none(cls, value: object) -> object:
        if value == "":
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
