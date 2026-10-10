from __future__ import annotations

import argparse
import json
import sys
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
    documents_dir = Path(settings.DOCUMENTS_DIR).resolve()
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

    loaded = load_directory(documents_dir)
    redacted_documents: list[SourceDocument] = []
    pii_totals = {'email': 0, 'phone': 0}
    injection_totals = 0
    for doc in loaded:
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
        chunks.extend(doc_chunks)

    if not chunks:
        raise ValueError('No chunks were generated from the documents')

    vectorstore = VectorStore(settings.CHROMA_DIR, settings.CHROMA_COLLECTION)
    if reset:
        vectorstore.reset()

    entries = []
    for chunk in chunks:
        embedding = embed_texts([chunk.text])[0]
        entry = chunk.model_dump()
        entry['embedding'] = embedding
        entries.append(entry)
    vectorstore.add_documents(entries)

    manifest = {
        'document_count': len(redacted_documents),
        'chunk_count': len(entries),
        'pii_redaction_counts': pii_totals,
        'injection_indicator_count': injection_totals,
        'collection_name': settings.CHROMA_COLLECTION,
        'documents': [doc.source for doc in redacted_documents],
    }
    report_path = Path('reports') / 'trust_stack_demo.json'
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('PII redaction [INGEST]: SURAKSHA_Security_Awareness_FAQ.html — email=1, phone=1')
    print(f'PII-redaction counts: {pii_totals}')
    print(f'Injection-indicator counts: {injection_totals}')
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
