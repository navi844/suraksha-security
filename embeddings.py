from __future__ import annotations

from typing import Any

from sentence_transformers import SentenceTransformer

from settings import settings

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        if settings.USE_OPENAI_EMBEDDINGS and settings.OPENAI_API_KEY:
            # OpenAI embedding support is optional; do not use the sentence-transformers loader
            # for text-embedding-3-small, because that model name is not a local HF repo.
            return _model  # type: ignore[return-value]
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def _embed_with_openai(texts: list[str]) -> list[list[float]]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if settings.USE_OPENAI_EMBEDDINGS and settings.OPENAI_API_KEY:
        return _embed_with_openai(texts)
    model = get_embedding_model()
    return model.encode(texts, convert_to_numpy=True).tolist()


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
