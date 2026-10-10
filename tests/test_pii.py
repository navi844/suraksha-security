from pii import redact_text


def test_redacts_email_and_phone():
    text = 'My email is arjun.mehta@example.com and my phone is +91 98765 43210.'
    result = redact_text(text, 'INPUT')
    assert result.redaction_occurred is True
    assert '[REDACTED_EMAIL]' in result.redacted_text
    assert '[REDACTED_PHONE]' in result.redacted_text
    assert 'example.com' not in result.redacted_text
    assert '98765' not in result.redacted_text


def test_redacts_output_mock_message():
    text = 'For urgent assistance contact Kavya Rao at kavya.rao@example.invalid or +91 00000 67890.'
    result = redact_text(text, 'OUTPUT')
    assert result.redacted_text == 'For urgent assistance contact Kavya Rao at [REDACTED_EMAIL] or [REDACTED_PHONE].'
