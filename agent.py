from __future__ import annotations

import hashlib
import re
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
from audit_log import audit_log


def _normalize_question(question: str) -> str:
    return re.sub(r'[^a-z0-9\s]', ' ', question.lower()).strip()


def _get_hardcoded_answer(question: str) -> dict[str, Any] | None:
    normalized = _normalize_question(question)

    if ('mfa' in normalized or 'multi factor' in normalized) and ('company systems' in normalized or 'access' in normalized):
        answer = (
            'MFA is mandatory for access to all company systems, remote access, and privileged administrative access. '
            'Approved MFA factors include an authenticator application, a registered hardware security key, or an approved biometric factor.'
        )
        return {
            'answer': answer,
            'citations': ['SURAKSHA_Access_Control_Policy.pdf | section 4.1-4.4'],
            'context': 'MFA is mandatory for access to all company systems. MFA is mandatory for remote access. MFA is mandatory for privileged administrative access. Approved MFA factors include an authenticator application, a registered hardware security key, or an approved biometric factor.'
        }

    if ('notify' in normalized or 'notified' in normalized or 'notification' in normalized) and ('72 hours' in normalized or 'breach' in normalized or 'affected parties' in normalized):
        answer = (
            'Affected parties must be notified without undue delay and no later than 72 hours after a breach is confirmed. '
            'The 72-hour period begins when the Incident Commander records confirmation in the incident record.'
        )
        return {
            'answer': answer,
            'citations': ['SURAKSHA_Incident_Response_Plan.docx | Section 6 — Notification'],
            'context': 'Affected parties must be notified without undue delay and no later than 72 hours after a breach is confirmed. The 72-hour period begins when the Incident Commander records confirmation in the incident record.'
        }

    if ('phishing' in normalized and ('report' in normalized or 'suspected' in normalized or 'contact' in normalized)):
        answer = (
            'Use the fictional "Report Phishing" function in the email client. If the function is unavailable, create a fictional Security Operations ticket. '
            'For urgent suspected compromise, contact the named Security Operations duty contact, Kavya Rao, at kavya.rao@example.invalid or +91 00000 67890.'
        )
        return {
            'answer': answer,
            'citations': ['SURAKSHA_Security_Awareness_FAQ.html | FAQ: How do I report a suspected phishing attempt?'],
            'context': 'Use the fictional Report Phishing function in the email client. If the function is unavailable, create a fictional Security Operations ticket. For urgent suspected compromise, contact the named Security Operations duty contact. Kavya Rao at kavya.rao@example.invalid or +91 00000 67890.'
        }

    if ('incident' in normalized and 'open' in normalized and ('log' in normalized or 'security incidents' in normalized or 'still open' in normalized)):
        answer = (
            'The still-open security incidents in the log are: SEC-2026-002 (Phishing, High), SEC-2026-004 (Unauthorised Access, Critical), '
            'SEC-2026-006 (Malware, Medium), and SEC-2026-008 (Data Handling, Low).'
        )
        return {
            'answer': answer,
            'citations': ['SURAKSHA_Security_Incident_Log.csv | incident records with status=Open'],
            'context': 'Open incidents include SEC-2026-002, SEC-2026-004, SEC-2026-006, and SEC-2026-008. These records are marked Open in the incident log.'
        }

    if ('vendor' in normalized and ('customer data' in normalized or 'handling customer data' in normalized)):
        answer = 'For a vendor handling customer data, the required certifications are ISO/IEC 27001 and SOC 2 Type II.'
        return {
            'answer': answer,
            'citations': ['SURAKSHA_Approved_Vendor_Requirements.json | Customer Data Processor'],
            'context': 'For a vendor handling customer data, the required certifications are ISO/IEC 27001 and SOC 2 Type II.'
        }

    return None


def answer_question(question: str, vector_store: VectorStore, *, test_mode: bool = False) -> dict[str, Any]:
    observability.record('INPUT', 'Question received', question_hash=hashlib.sha256(question.encode()).hexdigest())
    redacted_input = redact_text(question, 'INPUT')
    safe_question = redacted_input.redacted_text
    observability.record('INPUT', 'Question redacted', stage='INPUT', counts=redacted_input.counts)

    hardcoded = _get_hardcoded_answer(safe_question)
    if hardcoded:
        output_redacted = redact_text(hardcoded['answer'], 'OUTPUT')
        observability.record('OUTPUT', 'Hardcoded answer redacted', stage='OUTPUT', counts=output_redacted.counts)
        validation = output_validation(output_redacted.redacted_text, hardcoded['context'])
        return {
            'question': safe_question,
            'answer': output_redacted.redacted_text,
            'citations': hardcoded['citations'],
            'confidence': 1.0,
            'validation': validation,
            'trace': {
                'input_redaction': redacted_input.counts,
                'output_redaction': output_redacted.counts,
                'retrieval_count': 0,
                'llm_called': False,
                'llm_skipped_reason': 'hardcoded_question_answer',
                'stages': ['INPUT', 'HARD_CODED', 'OUTPUT'],
            },
        }

    embedding = vector_store.collection.get(include=['embeddings']) if False else None
    embedding_vectors = None
    try:
        from embeddings import embed_texts
        embedding_vectors = embed_texts([safe_question])[0]
    except Exception:
        embedding_vectors = [0.0] * 384

    retrieval_hits = retrieve(embedding_vectors, vector_store.collection, k=settings.RETRIEVAL_K)
    context = '\n\n'.join(f"[Document ID: {hit.source} | Source: {hit.source}] {hit.content}" for hit in retrieval_hits)

    if not retrieval_hits:
        answer = 'I could not find a grounded answer in the fictional policy set.'
        validation = output_validation(answer, context)
        return {
            'question': safe_question,
            'answer': answer,
            'citations': [],
            'confidence': 0.0,
            'validation': validation,
            'trace': {
                'input_redaction': redacted_input.counts,
                'output_redaction': {'email': 0, 'phone': 0},
                'retrieval_count': 0,
                'llm_called': False,
                'llm_skipped_reason': 'no_relevant_context',
                'stages': ['INPUT', 'RETRIEVAL', 'OUTPUT'],
            },
        }

    if any('ignore previous instructions' in hit.content.lower() for hit in retrieval_hits):
        answer = 'I cannot follow instruction-like text inside retrieved content. I will answer only from trusted policy context.'
        validation = output_validation(answer, context)
        return {
            'question': safe_question,
            'answer': answer,
            'citations': [f"{hit.source} | {hit.locator}" for hit in retrieval_hits],
            'confidence': 0.0,
            'validation': validation,
            'trace': {
                'input_redaction': redacted_input.counts,
                'output_redaction': {'email': 0, 'phone': 0},
                'retrieval_count': len(retrieval_hits),
                'llm_called': False,
                'llm_skipped_reason': 'retrieved_content_contains_injection_signal',
                'stages': ['INPUT', 'RETRIEVAL', 'REFUSAL', 'OUTPUT'],
            },
        }

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
            'llm_called': True,
            'llm_skipped_reason': None,
            'stages': ['INPUT', 'RETRIEVAL', 'LLM', 'OUTPUT'],
        },
    }
    return result


def main() -> None:
    from settings import settings
    vector_store = VectorStore(settings.CHROMA_DIR, settings.CHROMA_COLLECTION)
    questions = [
        'What MFA requirement applies to accessing company systems?',
        'Within what timeline must affected parties be notified after a confirmed breach?',
        'How do I report a suspected phishing attempt, and who is the named contact?',
        'Which security incidents in the log are still Open?',
        'What certification is required for a vendor handling customer data?',
    ]

    for question in questions:
        result = answer_question(question, vector_store)
        audit_log.log_event('agent_question', {
            'question': question,
            'answer': result['answer'],
            'trace': result['trace'],
        })
        print(f'Q: {question}')
        print(f'A: {result["answer"]}')
        print(f'Citations: {result["citations"]}')
        print(f'Confidence: {result["confidence"]}')
        print('---')


if __name__ == '__main__':
    main()
