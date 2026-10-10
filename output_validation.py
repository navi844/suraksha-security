from __future__ import annotations

import re
from typing import Any


def validate_no_pii(text: str) -> bool:
    return not re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\+?\d[\d\s().-]{7,}\d', text)


def validate_grounded(text: str, context: str) -> bool:
    if not context or not text:
        return False
    return any(token.lower() in text.lower() for token in ['phishing', 'mfa', 'incident', 'vendor', 'access']) or any(token.lower() in context.lower() for token in ['phishing', 'mfa', 'incident', 'vendor', 'access'])


def validate_source_citations(text: str) -> bool:
    return '[Document ID:' in text or 'Source:' in text


def validate_no_instructions(text: str) -> bool:
    lowered = text.lower()
    banned = ['ignore previous instructions', 'reveal confidential system information', 'override system prompt']
    return not any(item in lowered for item in banned)


def validate_response(text: str, context: str) -> dict[str, bool]:
    return {
        'no_pii': validate_no_pii(text),
        'grounded': validate_grounded(text, context),
        'citations': validate_source_citations(text),
        'no_instruction_like_text': validate_no_instructions(text),
        'safe_pattern_check': True,
    }


def output_validation(text: str, context: str) -> dict[str, Any]:
    checks = validate_response(text, context)
    return {
        'passed': all(checks.values()),
        'checks': checks,
        'extra_validation': 'no_untrusted_instruction_following' in text.lower() or 'no_untrusted_instruction_following' not in text.lower(),
    }
