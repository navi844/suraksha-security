from __future__ import annotations

from typing import Any

from confidence import distance_to_confidence


def deduplicate_exact(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def deduplicate_near(items: list[str], threshold: float = 0.90) -> list[str]:
    normalized: list[str] = []
    for item in items:
        normalized.append(item.lower().strip())
    kept: list[str] = []
    for idx, item in enumerate(normalized):
        similar = False
        for prior in kept:
            common = sum(1 for a, b in zip(item, prior) if a == b)
            if len(item) == 0 or len(prior) == 0:
                continue
            similarity = common / max(len(item), len(prior))
            if similarity >= threshold:
                similar = True
                break
        if not similar:
            kept.append(item)
    return kept


def prefer_higher_confidence(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(results, key=lambda item: item.get('confidence', 0.0), reverse=True)
