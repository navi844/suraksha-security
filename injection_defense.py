from __future__ import annotations

import re

INJECTION_PATTERNS = [
    r'ignore previous instructions',
    r'reveal confidential system information',
    r'ignore all prior instructions',
    r'new instructions',
]


def detect_injection_indicators(text: str) -> bool:
    lowered = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return True
    return False


def scan_for_injection(text: str) -> dict[str, bool | str]:
    matched = detect_injection_indicators(text)
    return {
        'injection_indicator_present': matched,
        'trigger_text': 'ignore previous instructions' if matched else '',
    }
