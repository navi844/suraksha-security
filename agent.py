from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from prompts import build_prompt
from pii import redact_text
from llm_client import llm_client
from output_validation import output_validation
from observability import observability
from retrieval import retrieve
from settings import settings
from vectorstore import VectorStore


def answer_question(question: str, vector_store: VectorStore, *, test_mode: bool = False) -> dict[str, Any]:
    observability.record('INPUT', 'Question received', question_hash=hashlib.sha256(question.encode()).hexdigest())
    redacted_input = redact_text(question, 'INPUT')
    safe_question = redacted_input.redacted_text
    observability.record('INPUT', 'Question redacted', stage='INPUT', counts=redacted_input.counts)

    embedding = vector_store.collection.get(include=['embeddings']) if False else None
    embedding_vectors = None
    try:
        from embeddings import embed_texts
        embedding_vectors = embed_texts([safe_question])[0]
    except Exception:
        embedding_vectors = [0.0] * 384

    retrieval_hits = retrieve(embedding_vectors, vector_store.collection, k=settings.RETRIEVAL_K)
    context = '\n\n'.join(f"[Document ID: {hit.source} | Source: {hit.source}] {hit.content}" for hit in retrieval_hits)
    prompt = build_prompt(safe_question, context)
    answer = llm_client.complete(prompt)

    output_redacted = redact_text(answer, 'OUTPUT')
    observability.record('OUTPUT', 'Answer redacted', stage='OUTPUT', counts=output_redacted.counts)
    validation = output_validation(output_redacted.redacted_text, context)
    result = {
        'question': safe_question,
        'answer': output_redacted.redacted_text,
        'citations': [f"{hit.source} | {hit.locator}" for hit in retrieval_hits],
        'confidence': sum(hit.confidence for hit in retrieval_hits) / max(1, len(retrieval_hits)),
        'validation': validation,
        'trace': {
            'input_redaction': redacted_input.counts,
            'output_redaction': output_redacted.counts,
            'retrieval_count': len(retrieval_hits),
            'stages': ['INPUT', 'RETRIEVAL', 'LLM', 'OUTPUT'],
        },
    }
    return result
