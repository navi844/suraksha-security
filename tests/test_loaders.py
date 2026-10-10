from pathlib import Path

from loaders import load_document, load_directory


def test_load_directory_generates_expected_file_count(project_root):
    docs = load_directory(project_root / 'documents')
    assert len(docs) >= 5
    assert any(doc.source.endswith('.pdf') for doc in docs)
    assert any(doc.source.endswith('.html') for doc in docs)
    assert any(doc.source.endswith('.csv') for doc in docs)
    assert any(doc.source.endswith('.json') for doc in docs)


def test_pdf_loader_extracts_text(project_root):
    pdf_docs = load_document(project_root / 'documents' / 'SURAKSHA_Access_Control_Policy.pdf')
    assert pdf_docs
    assert any('MFA' in doc.text for doc in pdf_docs)


def test_html_loader_keeps_phishing_text(project_root):
    html_docs = load_document(project_root / 'documents' / 'SURAKSHA_Security_Awareness_FAQ.html')
    assert html_docs
    assert 'ignore previous instructions' in html_docs[0].text.lower()
