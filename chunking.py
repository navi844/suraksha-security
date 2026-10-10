from __future__ import annotations

import hashlib
from typing import Any

from schemas import Chunk, SourceDocument


def normalize_text(text: str) -> str:
    return ' '.join(text.split())


def chunk_document(doc: SourceDocument, chunk_size: int = 700, overlap: int = 80) -> list[Chunk]:
    if not doc.text or not doc.text.strip():
        return []
    text = normalize_text(doc.text)
    parts = []
    start = 0
    index = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end]
        if not chunk_text.strip():
            break
        chunk_id = hashlib.sha256(f"{doc.source}:{doc.document_id}:{doc.locator_value or doc.source}:{index}".encode()).hexdigest()[:16]
        parts.append(
            Chunk(
                chunk_id=chunk_id,
                text=chunk_text,
                source=doc.source,
                document_id=doc.document_id,
                locator=doc.locator_value or doc.source,
                chunk_sequence=index,
                pii_redacted=doc.pii_redacted,
                pii_types=doc.pii_types,
                injection_indicator_present=doc.injection_indicator_present,
                content_hash=hashlib.sha256(chunk_text.encode()).hexdigest(),
                metadata={
                    'section': doc.section,
                    'page': doc.page,
                    'row_number': doc.row_number,
                    'record_id': doc.record_id,
                    'file_format': doc.file_format,
                    'effective_date': str(doc.effective_date) if doc.effective_date else None,
                },
            )
        )
        if end == len(text):
            break
        start = max(start + chunk_size - overlap, start + 1)
        index += 1
    return parts
