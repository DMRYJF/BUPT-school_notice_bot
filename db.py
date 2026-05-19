import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Iterable, Optional

from config import DB_PATH


def content_hash(content: str) -> str:
    normalized = (content or "").strip().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                publish_date TEXT,
                content TEXT,
                content_hash TEXT UNIQUE,
                summary TEXT,
                sent INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_notices_url ON notices(url)")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_notices_content_hash ON notices(content_hash)"
        )


def notice_exists(url: str, hash_value: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM notices WHERE url = ? OR content_hash = ? LIMIT 1",
            (url, hash_value),
        ).fetchone()
        return row is not None


def insert_notice(notice: Dict[str, str]) -> Optional[int]:
    hash_value = notice.get("content_hash") or content_hash(notice.get("content", ""))
    if notice_exists(notice["url"], hash_value):
        return None

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO notices (
                title, url, publish_date, content, content_hash, summary, sent, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                notice["title"],
                notice["url"],
                notice.get("publish_date", "unknown"),
                notice.get("content", ""),
                hash_value,
                notice.get("summary"),
                int(notice.get("sent", 0)),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        return int(cursor.lastrowid)


def update_summary(notice_id: int, summary: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE notices SET summary = ? WHERE id = ?", (summary, notice_id))


def mark_sent(notice_id: int) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE notices SET sent = 1 WHERE id = ?", (notice_id,))


def get_unsent_notices() -> Iterable[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM notices WHERE sent = 0 ORDER BY created_at ASC"
        ).fetchall()
        return rows
