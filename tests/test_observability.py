from observability import observability


def test_observability_records_stage_metadata():
    before = len(observability.events)
    observability.record('INPUT', 'question redacted', stage='INPUT', redaction={'email': 1})
    assert len(observability.events) == before + 1
    assert observability.events[-1]['stage'] == 'INPUT'
