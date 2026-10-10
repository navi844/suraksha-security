from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict


class RedactionStage(str, Enum):
    INGEST = 'INGEST'
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra='allow')

    text: str
    source: str
    document_id: str
    version: str
    effective_date: str | date | None = None
    file_format: str
    locator_type: str | None = None
    locator_value: str | None = None
    page: int | None = None
    section: str | None = None
    row_number: int | None = None
    record_id: str | None = None
    pii_redacted: bool = False
    pii_types: list[str] = Field(default_factory=list)
    injection_indicator_present: bool = False
    content_hash: str = ''


class Chunk(BaseModel):
    model_config = ConfigDict(extra='allow')

    chunk_id: str
    text: str
    source: str
    document_id: str
    locator: str
    chunk_sequence: int
    pii_redacted: bool = False
    pii_types: list[str] = Field(default_factory=list)
    injection_indicator_present: bool = False
    content_hash: str = ''
    metadata: dict[str, Any] = Field(default_factory=dict)


class RedactionResult(BaseModel):
    redacted_text: str
    redaction_occurred: bool
    counts: dict[str, int] = Field(default_factory=dict)
    stage: RedactionStage
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    chunk_id: str
    source: str
    locator: str
    raw_distance: float
    confidence: float
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class QuestionRequest(BaseModel):
    question: str
    context: str | None = None


class AnswerResponse(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    validation: dict[str, Any] = Field(default_factory=dict)
    trace: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    event_type: str
    timestamp: str
    detail: dict[str, Any] = Field(default_factory=dict)


class AgentTrace(BaseModel):
    stage: str
    messages: list[str] = Field(default_factory=list)
    redaction: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    status: str = 'ok'


class ComplianceEvidence(BaseModel):
    document_id: str
    source: str
    requirement: str
    status: Literal['pass', 'fail', 'pending']
    evidence: str
    reviewed_by: str = 'fictional compliance reviewer'
