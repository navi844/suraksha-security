from __future__ import annotations

from datetime import datetime, timezone


class Observability:
    def __init__(self):
        self.events: list[dict] = []

    def record(self, *args, **kwargs):
        if len(args) >= 2:
            stage, message = args[0], args[1]
        elif 'stage' in kwargs and 'message' in kwargs:
            stage = kwargs.pop('stage')
            message = kwargs.pop('message')
        elif 'stage' in kwargs:
            stage = kwargs.pop('stage')
            message = kwargs.pop('message', '')
        else:
            raise TypeError('observability.record requires a stage and message')

        payload = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': stage,
            'message': message,
            **kwargs,
        }
        self.events.append(payload)

    def snapshot(self):
        return {'events': self.events}


observability = Observability()
