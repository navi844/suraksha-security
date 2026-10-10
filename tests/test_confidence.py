from confidence import distance_to_confidence, confidence_bucket


def test_distance_to_confidence_maps_lower_distance_to_higher_confidence():
    assert distance_to_confidence(0.0) == 1.0
    assert distance_to_confidence(1.0) < 1.0


def test_confidence_bucket_works():
    assert confidence_bucket(0.8) == 'high'
    assert confidence_bucket(0.6) == 'medium'
    assert confidence_bucket(0.2) == 'low'
