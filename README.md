# Suraksha Security Policy Trust & Compliance Pipeline

Suraksha Security is a fictional, safety-focused RAG (retrieval-augmented generation) project designed for security-policy questions in a training environment. The system ingests policy documents, redacts PII, detects prompt-injection patterns, chunks content for retrieval, embeds it into a local vector database, and answers grounded questions with citations and validation metadata.

This project is intentionally built as a secure-by-design demo pipeline for a trust and compliance lab. It avoids real production data and uses fictional content only.

## Table of Contents

- Overview
- Project goals
- Repository structure
- Setup and installation
- Configuration
- Usage and API examples
- End-to-end execution flow
- Architecture overview
- Chunking strategy
- Retrieval and generation flow
- Testing the functionality
- Security and guardrail explanation
- Notes and limitations

## Overview

The system follows a standard trusted RAG pattern:

1. Load source documents from the `documents/` folder.
2. Normalize and sanitize text.
3. Redact PII (emails, phone numbers) before storing or answering.
4. Scan for prompt-injection indicators.
5. Split large documents into overlapping chunks.
6. Embed chunks using sentence-transformers or an OpenAI-compatible embedding model.
7. Store chunks in a local Chroma vector database.
8. Retrieve the most relevant chunks for a user question.
9. Combine the retrieved context with a system prompt.
10. Generate an answer using a local mock LLM or an OpenAI-compatible LLM.
11. Redact outputs again before returning to the user.
12. Validate the answer and log trace metadata for auditability.

## Project goals

- Build a trustworthy policy assistant using local-first components.
- Keep all generated responses grounded in the available policy documents.
- Protect against PII leakage through redaction at ingestion, input, and output.
- Detect prompt-injection language and prevent unsafe follow-through.
- Provide deterministic, testable behavior for training and grading scenarios.
- Produce traceable answers with citations, confidence scores, and validation results.

## Repository structure

```text
suraksha-security/
├── agent.py                  # Question-answer orchestration helper
├── app.py                   # FastAPI query endpoint
├── audit_log.py              # Audit logging utilities
├── audit_query_tool.py       # Query/audit helper tooling
├── build_vectorstore.py      # Vector store creation and ingestion pipeline
├── chunking.py               # Chunking logic for documents
├── compliance_checklist.md   # Compliance checklist / policy summary
├── confidence.py             # Confidence scoring functions
├── context.py                # Context management helpers
├── documents/                # Fictional sample policy documents
├── embeddings.py             # Embedding generation logic
├── injection_defense.py       # Prompt-injection detection
├── loaders.py                # Document loaders for PDFs, HTML, CSV, JSON, DOCX
├── llm_client.py             # Mock or OpenAI-compatible LLM wrapper
├── observability.py          # Structured telemetry and logging
├── output_validation.py      # Answer validation checks
├── pii.py                    # PII redaction service
├── prompts.py                # Prompt construction
├── retrieval.py              # Similarity retrieval logic
├── schemas.py                # Pydantic schemas for documents and chunks
├── scripts/
│   └── generate_sample_documents.py
├── settings.py               # Central app configuration
├── tests/                   # Unit and end-to-end tests
├── vectorstore.py            # Chroma wrapper for vector operations
├── requirements.txt          # Python dependencies
├── README.md                # Project documentation
├── REFLECTION.md             # Additional notes / reflections
└── reports/                  # Build manifests and demonstration output
```

## Setup and installation

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate fictional source documents

```bash
python scripts/generate_sample_documents.py
```

This creates or refreshes the sample policy data in `documents/`.

### 4. Build the vector store

```bash
python build_vectorstore.py --reset
```

This loads each document, performs redaction and injection checks, chunks the text, embeds each chunk, and stores the results in `chroma_store/`.

### 5. Start the API

```bash
uvicorn app:app --reload
```

The API is usually available at:

- `http://localhost:8000/health`
- `http://localhost:8000/query`

## Configuration

The default configuration is defined in `settings.py`.

Important settings include:

- `LLM_MODE`: `mock` or `openai_compatible`
- `CHROMA_DIR`: directory for local ChromaDB persistence
- `CHROMA_COLLECTION`: collection name used for embeddings
- `RETRIEVAL_K`: number of retrieved chunks
- `EMBEDDING_MODEL`: local embedding model name
- `OPENAI_API_KEY`: optional API key for OpenAI-compatible providers
- `USE_OPENAI_EMBEDDINGS`: toggled automatically if API key is present

Example environment variables:

```bash
LLM_MODE=mock
# or
LLM_MODE=openai_compatible
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-key
LLM_MODEL=gpt-4o-mini
```

When no key is configured, the project falls back to the local mock LLM behavior.

## Usage

### Query the API

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"How do I report a suspected phishing attempt?"}'
```

Example response structure:

```json
{
  "answer": "Report suspected phishing using the fictional Report Phishing function in the email client.",
  "citations": ["SURAKSHA_Security_Awareness_FAQ.html | section:faq"],
  "confidence": 0.82,
  "validation": {
    "grounded": true,
    "citation_count": 2,
    "status": "ok"
  },
  "trace": {
    "duration_ms": 142.3,
    "redaction": {
      "input": {"email": 0, "phone": 0},
      "output": {"email": 0, "phone": 0}
    },
    "stages": ["INPUT", "RETRIEVAL", "LLM", "OUTPUT"]
  }
}
```

### Health check

```bash
curl http://localhost:8000/health
```

### Use the helper function directly

```python
from agent import answer_question
from vectorstore import VectorStore
from settings import settings

vs = VectorStore(settings.CHROMA_DIR, settings.CHROMA_COLLECTION)
result = answer_question("How do I report a suspected phishing attempt?", vs)
print(result["answer"])
print(result["citations"])
```

## End-to-end execution process

The normal execution path for a user question is:

1. User sends a question to the API in `app.py`.
2. `QueryRequest` validates the payload.
3. `redact_text` removes emails and phone numbers before any retrieval or LLM call.
4. The question is embedded using `embed_texts([...])`.
5. The vector store is queried using similarity search.
6. Top matching chunks are retrieved.
7. A grounded prompt is constructed from the user question and the retrieved context.
8. The LLM generates a response.
9. The output is redacted again for safety.
10. Validation checks ensure the answer is grounded and consistent.
11. The result is logged to the audit trail and returned to the user.

This process is implemented in:

- `app.py` for the HTTP endpoint
- `agent.py` for direct programmatic orchestration
- `retrieval.py` for retrieval logic
- `llm_client.py` for generation backend selection
- `output_validation.py` for validation
- `audit_log.py` for trace logging

## Architecture overview

### 1. Ingestion layer

Documents are read from `documents/` using loaders in `loaders.py`. The project supports:

- PDF
- DOCX
- HTML
- CSV
- JSON

Each document is normalized into a structured `SourceDocument` model with metadata such as:

- source filename
- document ID
- section
- row number
- page
- record ID
- effective date
- file format

### 2. Trust and safety layer

Before the text is embedded or used in a prompt, the system enforces:

- PII redaction via `pii.py`
- Prompt-injection scanning via `injection_defense.py`
- Output redaction before returning answers
- Observability logs for each stage

This ensures that unsafe or sensitive text is neutralized before it enters downstream steps.

### 3. Chunking and retrieval layer

The system converts each normalized document into smaller chunks using `chunking.py`.

Each chunk includes metadata about:

- source document
- chunk sequence
- locator
- page / section references
- content hash
- prior safety flags

The chunk text is converted into embeddings and added to Chroma. Then user questions are embedded and compared against stored chunks using similarity search.

### 4. Generation layer

The retrieved context is combined with a prompt constructed in `prompts.py` and passed to the LLM. The system supports:

- local mock LLM for deterministic testing
- OpenAI-compatible API for real model usage

The LLM response is then passed back through output validation and redaction.

### 5. Observability and audit

The project records:

- request timing
- redaction counts
- retrieval hits
- stage transitions
- validation outcome
- audit events

This makes debugging and compliance review straightforward.

## Chunking strategy

The project uses a simple but effective chunking strategy in `chunking.py`.

### Current strategy

- `chunk_size = 600` characters
- `overlap = 120` characters
- normalized whitespace (`' '.join(text.split())`)
- chunk order preserved by section and sequence
- each chunk includes metadata like source, locator, and content hash

### Why this matters

This approach balances:

- retrieval granularity
- context preservation across boundaries
- manageable embedding size
- better handling of long policy documents

The overlap helps preserve continuity between adjacent chunks so important policy clauses are not lost at boundaries.

### Example chunking behavior

A long document is split into chunks like:

```text
Chunk 1: 600 chars + overlap
Chunk 2: next 600 chars with 120-char overlap
Chunk 3: next 600 chars with 120-char overlap
```

This allows the retriever to find relevant policy phrases even when they occur near the end of one chunk or the beginning of another.

## Retrieval and generation flow

The retrieval function in `retrieval.py` runs a similarity query against the vector database and converts Chroma distances to a confidence score using `confidence.py`.

Key behavior:

- `collection.query(query_embeddings=[query_embedding], n_results=k)`
- raw distance is transformed into a confidence value
- top results are returned with metadata and content
- duplicate or near-duplicate chunks are filtered if needed

The generation prompt is built with:

- the user question
- the retrieved context snippets
- a fixed instruction to answer using only the provided policy context

This makes the LLM answer more grounded and reduces hallucination risk.

## Testing the functionality

The project includes a test suite under `tests/`.

### Run all tests

```bash
pytest -q
```

### Run selected tests

```bash
pytest tests/test_end_to_end.py -q
pytest tests/test_guardrail.py -q
pytest tests/test_pii.py -q
```

### Test coverage areas

The tests validate:

- end-to-end question flow
- presence of sample documents
- PII redaction behavior
- injection detection
- answer validation / guardrails
- observability and audit flow

### Example test files

- `tests/test_end_to_end.py`: checks a realistic user question and verifies answer generation
- `tests/test_guardrail.py`: validates that injection-like text is detected
- `tests/test_pii.py`: verifies redaction of email and phone patterns
- `tests/test_output_validation.py`: ensures answer validation logic behaves as expected

## Security and guardrail explanation

This repository follows several explicit trust controls:

### PII redaction

`pii.py` uses regex-based detection for:

- email addresses
- phone numbers

These are replaced with placeholders such as:

- `[REDACTED_EMAIL]`
- `[REDACTED_PHONE]`

Redaction occurs at:

- ingestion stage
- user-input stage
- output stage

This prevents sensitive contact data from entering logs or responses.

### Prompt-injection defense

`injection_defense.py` checks for common injection patterns like:

- "ignore previous instructions"
- "ignore all prior instructions"
- "reveal confidential system information"
- "new instructions"

If detected, the system tags the content as unsafe and never follows those instructions.

### Grounding and validation

`output_validation.py` evaluates outputs against the retrieved context to reduce unsupported answers. The result contains metadata about whether the response is grounded and whether citation context is sufficient.

### Local-first design

By default, the system uses a mock LLM and local embedding model. This makes it suitable for demonstrations and structured lab scenarios without requiring external secret management.

## Execution notes

### Typical development flow

```bash
python scripts/generate_sample_documents.py
python build_vectorstore.py --reset
uvicorn app:app --reload
```

Then send a question using the API.

### Sample question examples

- "How do I report a suspected phishing attempt?"
- "What certifications are required for vendors handling customer data?"
- "What should I do during a suspected security incident?"
- "Which policy covers access control?"

## Notes and limitations

- This is a fictional training project and not connected to any real enterprise environment.
- The mock LLM is intentionally deterministic and simplified.
- The project uses locally stored documents and a local Chroma database in development mode.
- The retrieval pipeline is intentionally practical and transparent rather than production-scale.
- It is designed for clarity, trust, and testing rather than high-throughput enterprise deployment.

## Security policy summary

The repository treats all generated content as fictional training-only material. It supports redaction, injection detection, and auditable responses, which is essential for a safe trust-and-compliance lab setup.

## Final summary

Suraksha Security demonstrates a complete, educational secure RAG pipeline that includes:

- document ingestion
- PII protection
- injection defense
- semantic retrieval
- grounded answer generation
- output validation
- audit logging
- testable behavior

This makes it a strong reference implementation for learning trustworthy AI workflows and policy-assisted assistants.
