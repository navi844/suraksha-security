# Reflection

This project follows a safe, local-first RAG architecture for fictional policy analysis. It uses deterministic mock LLM behavior for tests and keeps the embedding path isolated from the LLM provider. The redaction pipeline, prompt-injection scanner, and evidence-backed answer validation are designed to stay aligned with the assignment's emphasis on trust, safety, and auditability.

Important notes:
- All data is fictional training content.
- Raw PII is never stored or logged.
- Retrieved document content is treated as untrusted data.
- Any malicious instruction-like text is detected and not followed.
- Local execution is used whenever possible; any missing evidence is labeled as pending local execution.
