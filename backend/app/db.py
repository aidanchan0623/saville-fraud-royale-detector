import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings


def _sqlite_path() -> Path:
    url = settings.database_url
    if url.startswith("sqlite:///"):
        return Path(url.replace("sqlite:///", "", 1)).resolve()
    return Path("reports.sqlite3").resolve()


def init_db() -> None:
    path = _sqlite_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS report_cache (
              cache_key TEXT PRIMARY KEY,
              payload TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )


def get_cached_report(cache_key: str) -> dict[str, Any] | None:
    path = _sqlite_path()
    if not path.exists():
        return None
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT payload FROM report_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
    return json.loads(row[0]) if row else None


def save_cached_report(cache_key: str, payload: dict[str, Any]) -> None:
    path = _sqlite_path()
    init_db()
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO report_cache(cache_key, payload, created_at)
            VALUES (?, ?, ?)
            """,
            (
                cache_key,
                json.dumps(payload),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

