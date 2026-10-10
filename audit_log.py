from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from settings import settings


class AuditLog:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or settings.audit_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    detail TEXT NOT NULL
                )
                '''
            )

    def log_event(self, event_type: str, detail: dict | str) -> None:
        payload = detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=True, sort_keys=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO audit_events (timestamp, event_type, detail) VALUES (?, ?, ?)',
                (datetime.now(timezone.utc).isoformat(), event_type, payload),
            )

    def query(self, event_type: str | None = None, limit: int = 20):
        with sqlite3.connect(self.db_path) as conn:
            if event_type:
                rows = conn.execute(
                    'SELECT timestamp, event_type, detail FROM audit_events WHERE event_type = ? ORDER BY id DESC LIMIT ?',
                    (event_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    'SELECT timestamp, event_type, detail FROM audit_events ORDER BY id DESC LIMIT ?',
                    (limit,),
                ).fetchall()
        return [
            {'timestamp': timestamp, 'event_type': event_type_name, 'detail': json.loads(detail)}
            for timestamp, event_type_name, detail in rows
        ]


audit_log = AuditLog()
