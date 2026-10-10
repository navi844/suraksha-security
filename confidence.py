from __future__ import annotations

from settings import settings


def distance_to_confidence(distance: float) -> float:
    """Converts Chroma L2 distance to a bounded confidence score.
    Lower distance means more relevant, so we map smaller values to higher confidence.
    """
    if distance <= 0:
        return 1.0
    normalized = max(0.0, min(1.0, 1.0 / (1.0 + distance)))
    return round(normalized, 4)


def confidence_bucket(confidence: float) -> str:
    if confidence >= settings.HIGH_CONFIDENCE_SCORE:
        return 'high'
    if confidence >= settings.MEDIUM_CONFIDENCE_SCORE:
        return 'medium'
    return 'low'
