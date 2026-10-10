from __future__ import annotations

import re
from typing import Any

from schemas import RedactionResult, RedactionStage

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")


class PIIService:
    def redact_text(self, text: str, stage: str = RedactionStage.INGEST.value) -> RedactionResult:
        redacted = text
        counts: dict[str, int] = {'email': 0, 'phone': 0}
        redaction_occurred = False

        email_matches = EMAIL_RE.findall(redacted)
        if email_matches:
            redacted = EMAIL_RE.sub('[REDACTED_EMAIL]', redacted)
            counts['email'] = len(email_matches)
            redaction_occurred = True

        phone_matches = PHONE_RE.findall(redacted)
        if phone_matches:
            replacement = re.sub(r'\d', 'X', phone_matches[0]) if False else '[REDACTED_PHONE]'
            redacted = PHONE_RE.sub('[REDACTED_PHONE]', redacted)
            counts['phone'] = len(phone_matches)
            redaction_occurred = True

        return RedactionResult(
            redacted_text=redacted,
            redaction_occurred=redaction_occurred,
            counts=counts,
            stage=RedactionStage(stage),
            metadata={
                'stage': stage,
                'redaction_tokens': ['[REDACTED_EMAIL]', '[REDACTED_PHONE]'],
                'safe': True,
            },
        )


pii_service = PIIService()


def redact_text(text: str, stage: str = RedactionStage.INGEST.value) -> RedactionResult:
    return pii_service.redact_text(text, stage)


def redact_texts(texts: list[str], stage: str = RedactionStage.INGEST.value) -> list[RedactionResult]:
    return [redact_text(text, stage) for text in texts]
