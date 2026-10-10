from __future__ import annotations

from datetime import datetime, timezone


class Observability:
    def __init__(self):
        self.events: list[dict] = []

    def record(self, stage: str, message: str, **kwargs):
        self.events.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': stage,
            'message': message,
            **kwargs,
        })

    def snapshot(self):
        return {'events': self.events}


observability = Observability()
