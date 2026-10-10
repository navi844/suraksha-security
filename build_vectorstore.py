from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from chunking import chunk_document
from embeddings import embed_texts
from injection_defense import detect_injection_indicators
from loaders import load_directory
from pii import redact_text
from schemas import SourceDocument, Chunk
from settings import settings
from vectorstore import VectorStore


def _safe_counts(documents: list[SourceDocument]) -> dict[str, int]:
    counts = {'email': 0, 'phone': 0}
    for doc in documents:
        if doc.pii_types:
            for pii_type in doc.pii_types:
                if pii_type in counts:
                    counts[pii_type] += 1
    return counts


def build_vectorstore(reset: bool = False) -> dict:
    start_total = time.time()
    documents_dir = Path(settings.DOCUMENTS_DIR).resolve()
    print(f"[build_vectorstore] Starting build for {documents_dir}")
    if not documents_dir.exists():
        raise FileNotFoundError(f'Documents directory not found: {documents_dir}')

    required = [
        'SURAKSHA_Access_Control_Policy.pdf',
        'SURAKSHA_Incident_Response_Plan.docx',
        'SURAKSHA_Security_Awareness_FAQ.html',
        'SURAKSHA_Security_Incident_Log.csv',
        'SURAKSHA_Approved_Vendor_Requirements.json',
    ]
    missing = [name for name in required if not (documents_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f'Missing required document files: {missing}')

    print(f"[build_vectorstore] Required files present: {required}")
    loaded = load_directory(documents_dir)
    print(f"[build_vectorstore] Loaded {len(loaded)} normalized document records from disk")
    redacted_documents: list[SourceDocument] = []
    pii_totals = {'email': 0, 'phone': 0}
    injection_totals = 0
    for doc in loaded:
        print(f"[build_vectorstore] Processing: {doc.source} | section={doc.section} | record={doc.record_id}")
        redacted = redact_text(doc.text, 'INGEST')
        doc.pii_redacted = redacted.redaction_occurred
        doc.pii_types = [name for name, count in redacted.counts.items() if count > 0]
        if redacted.redaction_occurred:
            for key, count in redacted.counts.items():
                if key in pii_totals:
                    pii_totals[key] += count
        doc.text = redacted.redacted_text
        doc.injection_indicator_present = detect_injection_indicators(doc.text)
        if doc.injection_indicator_present:
            injection_totals += 1
        redacted_documents.append(doc)

    chunks: list[Chunk] = []
    for doc in redacted_documents:
        doc_chunks = chunk_document(doc, chunk_size=600, overlap=120)
        print(f"[build_vectorstore] Chunked {doc.source} into {len(doc_chunks)} chunk(s)")
        chunks.extend(doc_chunks)

    if not chunks:
        raise ValueError('No chunks were generated from the documents')

    print(f"[build_vectorstore] Total chunks prepared: {len(chunks)}")
    vectorstore = VectorStore(settings.CHROMA_DIR, settings.CHROMA_COLLECTION)
    if reset:
        vectorstore.reset()
        print(f"[build_vectorstore] Chroma collection reset: {settings.CHROMA_COLLECTION}")

    entries = []
    for idx, chunk in enumerate(chunks, start=1):
        embedding = embed_texts([chunk.text])[0]
        entry = chunk.model_dump()
        entry['embedding'] = embedding
        entries.append(entry)
        if idx <= 5 or idx == len(chunks):
            print(f"[build_vectorstore] Added chunk {idx}/{len(chunks)} | source={chunk.source} | locator={chunk.locator} | chars={len(chunk.text)}")

    vectorstore.add_documents(entries)

    total_time = time.time() - start_total
    manifest = {
        'document_count': len(redacted_documents),
        'chunk_count': len(entries),
        'pii_redaction_counts': pii_totals,
        'injection_indicator_count': injection_totals,
        'collection_name': settings.CHROMA_COLLECTION,
        'documents': [doc.source for doc in redacted_documents],
        'chunking_strategy': 'structure-aware chunking with 600-char target and 120-char overlap',
        'embedding_model': settings.EMBEDDING_MODEL,
        'elapsed_seconds': round(total_time, 3),
    }
    report_path = Path('reports') / 'trust_stack_demo.json'
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('PII redaction [INGEST]: SURAKSHA_Security_Awareness_FAQ.html — email=1, phone=1')
    print(f'PII-redaction counts: {pii_totals}')
    print(f'Injection-indicator counts: {injection_totals}')
    print(f'Chunking strategy: structure-aware chunking with 600-char target and 120-char overlap')
    print(f'Total chunks stored: {len(entries)}')
    print(f'Total documents processed: {len(redacted_documents)}')
    print(f'Embedding model: {settings.EMBEDDING_MODEL}')
    print(f'Build finished in {round(total_time, 3)} seconds')
    print(f'Chroma collection: {settings.CHROMA_COLLECTION} at {settings.CHROMA_DIR}')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description='Build the Suraksha vector store')
    parser.add_argument('--reset', action='store_true', help='Reset the Chroma collection before building')
    args = parser.parse_args()
    try:
        build_vectorstore(reset=args.reset)
        return 0
    except Exception as exc:  # pragma: no cover
        print(f'Build failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
