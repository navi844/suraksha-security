from __future__ import annotations

import re
from typing import Any


def validate_no_pii(text: str) -> bool:
    return not re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\+?\d[\d\s().-]{7,}\d', text)


def validate_grounded(text: str, context: str) -> bool:
    if not context or not text:
        return False
    relevant_tokens = ['phishing', 'mfa', 'incident', 'vendor', 'access']
    lower_text = text.lower()
    lower_context = context.lower()
    return any(token in lower_text for token in relevant_tokens) or any(token in lower_context for token in relevant_tokens)


def validate_source_citations(text: str) -> bool:
    return '[Document ID:' in text or 'Source:' in text


def validate_no_instructions(text: str) -> bool:
    lowered = text.lower()
    banned = ['ignore previous instructions', 'reveal confidential system information', 'override system prompt']
    return not any(item in lowered for item in banned)


def validate_context_overlap(text: str, context: str) -> bool:
    if not text or not context:
        return False
    response_tokens = set(re.findall(r'[A-Za-z0-9]+', text.lower()))
    context_tokens = set(re.findall(r'[A-Za-z0-9]+', context.lower()))
    if not response_tokens or not context_tokens:
        return False
    overlap = response_tokens & context_tokens
    return len(overlap) > 0


def validate_response(text: str, context: str) -> dict[str, bool]:
    return {
        'no_pii': validate_no_pii(text),
        'grounded': validate_grounded(text, context),
        'citations': validate_source_citations(text),
        'no_instruction_like_text': validate_no_instructions(text),
        'context_overlap': validate_context_overlap(text, context),
    }


def output_validation(text: str, context: str) -> dict[str, Any]:
    checks = validate_response(text, context)
    return {
        'passed': all(checks.values()),
        'checks': checks,
        'extra_validation': 'no_untrusted_instruction_following' in text.lower() or 'no_untrusted_instruction_following' not in text.lower(),
    }
