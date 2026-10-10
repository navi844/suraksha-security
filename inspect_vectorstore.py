from __future__ import annotations

import argparse
import json

from settings import settings
from vectorstore import VectorStore


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect the Suraksha Chroma collection')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()

    store = VectorStore(settings.CHROMA_DIR, settings.CHROMA_COLLECTION)
    results = store.collection.query(query_embeddings=[[0.0] * 384], n_results=args.limit)
    records = []
    for idx, doc in enumerate(results.get('documents', [[]])[0]):
        metadata = results.get('metadatas', [[]])[0][idx]
        records.append({'id': results.get('ids', [[]])[0][idx], 'source': metadata.get('source'), 'document_id': metadata.get('document_id'), 'locator': metadata.get('locator'), 'snippet': doc[:200]})
    print(json.dumps(records, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
