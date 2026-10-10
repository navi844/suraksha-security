from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from settings import settings


class VectorStore:
    def __init__(self, persist_directory: str | Path | None = None, collection_name: str | None = None):
        self.persist_directory = str(persist_directory or settings.CHROMA_DIR)
        self.collection_name = collection_name or settings.CHROMA_COLLECTION
        self.client = chromadb.PersistentClient(path=self.persist_directory, settings=ChromaSettings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "l2"},
        )

    def add_documents(self, chunks: list[dict[str, Any]]) -> None:
        if not chunks:
            return
        ids = [chunk['chunk_id'] for chunk in chunks]
        texts = [chunk['text'] for chunk in chunks]
        embeddings = [chunk['embedding'] for chunk in chunks]
        metadata = [{
            'source': chunk.get('source'),
            'document_id': chunk.get('document_id'),
            'locator': chunk.get('locator'),
            'chunk_sequence': str(chunk.get('chunk_sequence', 0)),
            'pii_redacted': str(bool(chunk.get('pii_redacted'))),
            'pii_types': json.dumps(chunk.get('pii_types', [])),
            'injection_indicator_present': str(bool(chunk.get('injection_indicator_present'))),
            'content_hash': chunk.get('content_hash'),
        } for chunk in chunks]
        self.collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadata)

    def query(self, query_embedding: list[float], n_results: int = 5):
        return self.collection.query(query_embeddings=[query_embedding], n_results=n_results)

    def count(self) -> int:
        return self.collection.count()

    def reset(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "l2"},
        )


vector_store = VectorStore()
