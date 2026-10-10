# Suraksha Security Policy Trust & Compliance Pipeline

This repository implements a fictional, safe RAG system for IT security policy questions. It is built as a graded take-home assignment inspired by a trust-and-compliance lab pattern.

## Features

- Local ChromaDB-backed vector store with sentence-transformers
- PII redaction at ingestion, input, and output stages
- Prompt-injection detection and explicit untrusted-content handling
- Confidence scoring and retrieval context filtering
- Local mock LLM and optional OpenAI-compatible provider configuration
- Audit logging and observability for each stage
- Grounded answers with citations and validation checks
- deterministic sample document generation

## Setup

1. Create a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` if needed.
4. Generate the fictional source documents: `python scripts/generate_sample_documents.py`
5. Build the vector store: `python build_vectorstore.py --reset`
6. Start the API: `uvicorn app:app --reload`

## Example query

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"How do I report a suspected phishing attempt?"}'
```

## Security notes

- All generated data is fictional training-only.
- Original PII is redacted before embedding and not stored in logs.
- Prompt-injection strings are detected but never followed.
- This repository does not contain real company data or confidential production information.
