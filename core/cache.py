"""SQLite cache with TTL support for research data."""
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from core.config import CACHE_PATH, CACHE_TTL_SECONDS, CACHE_TTL_SHORT_SECONDS


class Cache:
    """Simple SQLite-backed key-value cache with TTL."""

    def __init__(self, path: Path = CACHE_PATH):
        self.path = path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)"
            )
            conn.commit()

    def _key(self, namespace: str, identifier: str) -> str:
        raw = f"{namespace}:{identifier}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, namespace: str, identifier: str) -> Optional[Any]:
        key = self._key(namespace, identifier)
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute(
                "SELECT value FROM cache WHERE key = ? AND expires_at > ?",
                (key, time.time()),
            )
            row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def set(
        self,
        namespace: str,
        identifier: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        key = self._key(namespace, identifier)
        ttl = ttl_seconds if ttl_seconds is not None else CACHE_TTL_SECONDS
        expires_at = time.time() + ttl
        serialized = json.dumps(value, default=str)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache (key, value, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (key, serialized, expires_at, time.time()),
            )
            conn.commit()

    def invalidate(self, namespace: str, identifier: str) -> None:
        key = self._key(namespace, identifier)
        with sqlite3.connect(self.path) as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()

    def clear_expired(self) -> int:
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute(
                "DELETE FROM cache WHERE expires_at <= ?", (time.time(),)
            )
            conn.commit()
            return cur.rowcount

    def clear_all(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()


cache = Cache()
