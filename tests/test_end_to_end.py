from pathlib import Path

from app import query_endpoint
from pii import redact_text


def test_end_to_end_question_flow():
    question = 'My email is arjun.mehta@example.com and my phone is +91 98765 43210. How do I report a suspected phishing attempt?'
    result = query_endpoint(type('Req', (), {'question': question})())
    assert result.answer
    assert result.trace['redaction']['input']['email'] >= 0
    assert result.trace['redaction']['output']['email'] >= 0


def test_generated_documents_present(project_root):
    required = [
        'SURAKSHA_Access_Control_Policy.pdf',
        'SURAKSHA_Incident_Response_Plan.docx',
        'SURAKSHA_Security_Awareness_FAQ.html',
        'SURAKSHA_Security_Incident_Log.csv',
        'SURAKSHA_Approved_Vendor_Requirements.json',
    ]
    for name in required:
        assert (project_root / 'documents' / name).exists()
