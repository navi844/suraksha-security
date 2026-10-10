from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from audit_log import audit_log
from embeddings import embed_texts
from observability import observability
from output_validation import output_validation
from pii import redact_text
from prompts import build_prompt
from retrieval import retrieve
from settings import settings
from vectorstore import VectorStore

app = FastAPI(title='Suraksha Security Policy Assistant')


class QueryRequest(BaseModel):
    question: str
    user_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[str]
    confidence: float
    validation: dict[str, Any]
    trace: dict[str, Any]


vector_store = VectorStore(settings.CHROMA_DIR, settings.CHROMA_COLLECTION)


@app.get('/health')
def health() -> dict:
    return {'status': 'ok', 'collection': settings.CHROMA_COLLECTION}


@app.post('/query', response_model=QueryResponse)
def query_endpoint(payload: QueryRequest) -> QueryResponse:
    start = time.time()
    observability.record('INPUT', 'Received question', question_hash='redacted')

    input_redacted = redact_text(payload.question, 'INPUT')
    safe_question = input_redacted.redacted_text
    observability.record('INPUT', 'Redacted incoming question', redaction=input_redacted.counts, stage='INPUT')

    if not safe_question or not safe_question.strip():
        raise HTTPException(status_code=400, detail='Question is empty after redaction')

    q_embedding = embed_texts([safe_question])[0]
    hits = retrieve(q_embedding, vector_store.collection, k=settings.RETRIEVAL_K)
    if not hits:
        answer = 'I could not find a grounded answer in the fictional policy set.'
        citations = []
        confidence = 0.0
    else:
        context = '\n\n'.join(f"[Document ID: {item.source} | Source: {item.source}] {item.content}" for item in hits)
        prompt = build_prompt(safe_question, context)
        from llm_client import llm_client

        answer = llm_client.complete(prompt)
        citations = [f"{hit.source} | {hit.locator}" for hit in hits]
        confidence = sum(hit.confidence for hit in hits) / max(1, len(hits))

    output_redacted = redact_text(answer, 'OUTPUT')
    observability.record('OUTPUT', 'Redacted outgoing answer', redaction=output_redacted.counts, stage='OUTPUT')
    validation = output_validation(output_redacted.redacted_text, safe_question)
    response = QueryResponse(
        answer=output_redacted.redacted_text,
        citations=citations,
        confidence=confidence,
        validation=validation,
        trace={
            'duration_ms': round((time.time() - start) * 1000, 2),
            'redaction': {'input': input_redacted.counts, 'output': output_redacted.counts},
            'stages': ['INPUT', 'RETRIEVAL', 'LLM', 'OUTPUT'],
        },
    )
    audit_log.log_event('query', {'question': safe_question, 'response': output_redacted.redacted_text, 'trace': response.trace})
    return response
