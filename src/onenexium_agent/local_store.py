from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class LocalQueue:
    """Durable SQLite queue for samples when offline."""

    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._lock = threading.Lock()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  payload TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def enqueue(self, sample_dict: dict[str, Any]) -> None:
        blob = json.dumps(sample_dict, separators=(",", ":"))
        with self._lock, self._connect() as conn:
            conn.execute("INSERT INTO pending (payload) VALUES (?)", (blob,))
            conn.commit()

    def fetch_batch(self, limit: int) -> list[tuple[int, dict[str, Any]]]:
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "SELECT id, payload FROM pending ORDER BY id ASC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        out: list[tuple[int, dict[str, Any]]] = []
        for row_id, payload in rows:
            out.append((row_id, json.loads(payload)))
        return out

    def delete_ids(self, ids: list[int]) -> None:
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        with self._lock, self._connect() as conn:
            conn.execute(f"DELETE FROM pending WHERE id IN ({placeholders})", ids)
            conn.commit()

    def pending_count(self) -> int:
        with self._lock, self._connect() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM pending")
            row = cur.fetchone()
            return int(row[0]) if row else 0
