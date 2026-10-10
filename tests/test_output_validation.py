from output_validation import output_validation


def test_output_validation_flags_pii_and_missing_citations():
    text = 'Contact kavya.rao@example.invalid for help.'
    context = 'Safety guidance policy' 
    result = output_validation(text, context)
    assert result['checks']['no_pii'] is False
    assert result['passed'] is False
