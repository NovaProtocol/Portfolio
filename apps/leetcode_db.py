from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "leetcode_data.db"
_local = threading.local()


def get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leetcode_submissions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            title_slug TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leetcode_snapshot (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_snapshot(key: str, value: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO leetcode_snapshot (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (key, value),
    )
    conn.commit()


def get_snapshot(key: str) -> str | None:
    conn = get_conn()
    row = conn.execute("SELECT value FROM leetcode_snapshot WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def upsert_submissions(submissions: list[dict]) -> int:
    conn = get_conn()
    new_count = 0
    for sub in submissions:
        conn.execute(
            "INSERT OR IGNORE INTO leetcode_submissions (id, title, title_slug, timestamp, date) VALUES (?, ?, ?, ?, ?)",
            (sub["id"], sub["title"], sub["slug"], sub["timestamp"], sub["date"]),
        )
        if conn.execute("SELECT changes()").fetchone()[0] > 0:
            new_count += 1
    conn.commit()
    return new_count


def get_all_submissions() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, title_slug, timestamp, date FROM leetcode_submissions ORDER BY timestamp DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_submission_count() -> int:
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) as c FROM leetcode_submissions").fetchone()
    return row["c"] if row else 0
