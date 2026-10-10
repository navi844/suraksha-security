from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )

    APP_ENV: str = 'development'
    DOCUMENTS_DIR: str = './documents'
    CHROMA_DIR: str = './chroma_store'
    CHROMA_COLLECTION: str = 'suraksha_security_policies'
    AUDIT_DB_PATH: str = './audit_log.db'

    EMBEDDING_MODEL: str = 'all-MiniLM-L6-v2'
    USE_OPENAI_EMBEDDINGS: bool = True

    OPENAI_API_KEY: str = ''
    OPENAI_MODEL: str = 'gpt-4o-mini'
    OPENAI_EMBEDDING_MODEL: str = 'text-embedding-3-small'

    LLM_MODE: Literal['mock', 'openai_compatible'] = 'openai_compatible'
    LLM_BASE_URL: str = 'https://api.openai.com/v1'
    LLM_API_KEY: str = ''
    LLM_MODEL: str = 'gpt-4o-mini'

    RETRIEVAL_K: int = 5
    RETRIEVAL_CANDIDATES: int = 10
    MIN_CONFIDENCE_SCORE: float = 0.45
    HIGH_CONFIDENCE_SCORE: float = 0.75
    MEDIUM_CONFIDENCE_SCORE: float = 0.55
    MAX_CONTEXT_CHARS: int = 7000
    NEAR_DUPLICATE_THRESHOLD: float = 0.90
    REQUEST_TIMEOUT_SECONDS: int = 60
    SLOW_REQUEST_THRESHOLD_MS: int = 2000
    LOG_LEVEL: str = 'INFO'

    def model_post_init(self, __context):
        if self.OPENAI_API_KEY:
            self.LLM_BASE_URL = 'https://api.openai.com/v1'
            self.LLM_API_KEY = self.OPENAI_API_KEY
            self.LLM_MODEL = self.OPENAI_MODEL or 'gpt-4o-mini'
            self.USE_OPENAI_EMBEDDINGS = True
            self.EMBEDDING_MODEL = self.OPENAI_EMBEDDING_MODEL
        else:
            self.USE_OPENAI_EMBEDDINGS = False
            self.EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

    @property
    def documents_dir(self) -> Path:
        return Path(self.DOCUMENTS_DIR).resolve()

    @property
    def chroma_dir(self) -> Path:
        return Path(self.CHROMA_DIR).resolve()

    @property
    def audit_db_path(self) -> Path:
        return Path(self.AUDIT_DB_PATH).resolve()


settings = Settings()

if settings.LLM_MODE == 'openai_compatible':
    missing = []
    if not settings.LLM_BASE_URL:
        missing.append('LLM_BASE_URL')
    if not settings.LLM_API_KEY:
        missing.append('LLM_API_KEY')
    if not settings.LLM_MODEL:
        missing.append('LLM_MODEL')
    if missing:
        raise ValueError(
            'OpenAI-compatible LLM mode selected without required configuration: '
            + ', '.join(missing)
        )

