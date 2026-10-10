from audit_log import audit_log


def test_audit_log_can_store_event():
    audit_log.log_event('test', {'message': 'unit test event'})
    rows = audit_log.query(limit=5)
    assert any(row['event_type'] == 'test' for row in rows)
