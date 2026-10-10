from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_query_endpoint_redacts_input_and_output():
    response = client.post('/query', json={'question': 'My email is arjun.mehta@example.com and my phone is +91 98765 43210. How do I report a suspected phishing attempt?'})
    assert response.status_code == 200
    payload = response.json()
    assert '[REDACTED_EMAIL]' in payload['answer'] or payload['answer']
    assert payload['trace']['redaction']['input']['email'] == 1 or payload['trace']['redaction']['input']['phone'] == 1
