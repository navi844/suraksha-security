import os
from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def env_setup(monkeypatch, project_root):
    monkeypatch.setenv('DOCUMENTS_DIR', str(project_root / 'documents'))
    monkeypatch.setenv('CHROMA_DIR', str(project_root / 'chroma_store'))
    monkeypatch.setenv('AUDIT_DB_PATH', str(project_root / 'audit_log.db'))
    monkeypatch.setenv('LLM_MODE', 'mock')
    return project_root
