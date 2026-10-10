from __future__ import annotations

import math
from typing import Any

from confidence import distance_to_confidence
from schemas import RetrievalResult


def normalize_distance(distance: float) -> float:
    return max(0.0, float(distance))


def retrieve(query_embedding: list[float], collection: Any, k: int = 5) -> list[RetrievalResult]:
    results = collection.query(query_embeddings=[query_embedding], n_results=k)
    hits = []
    if not results or not results.get('documents'):
        return hits

    documents = results.get('documents', [[]])[0]
    distances = results.get('distances', [[]])[0]
    ids = results.get('ids', [[]])[0]
    metadatas = results.get('metadatas', [[]])[0]

    for idx, document in enumerate(documents):
        distance = normalize_distance(float(distances[idx]) if idx < len(distances) else 0.0)
        confidence = distance_to_confidence(distance)
        metadata = metadatas[idx] if idx < len(metadatas) else {}
        hits.append(
            RetrievalResult(
                chunk_id=ids[idx],
                source=str(metadata.get('source', 'unknown')),
                locator=str(metadata.get('locator', 'unknown')),
                raw_distance=distance,
                confidence=confidence,
                content=document,
                metadata=metadata,
            )
        )
    return hits


def build_context(results: list[RetrievalResult], max_chars: int = 7000) -> str:
    unique = []
    seen = set()
    for result in results:
        if result.content in seen:
            continue
        seen.add(result.content)
        unique.append(result)

    context_parts = []
    current_chars = 0
    for result in unique:
        snippet = f"[Source: {result.source} | Locator: {result.locator}]\n{result.content}\n"
        if current_chars + len(snippet) > max_chars:
            break
        context_parts.append(snippet)
        current_chars += len(snippet)
    return '\n'.join(context_parts)
