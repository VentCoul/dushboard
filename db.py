"""SQLite для dashboard-native даних: звички + кеш зовнішніх API.

Патерн узятий з core/database.py poster_buyer: один connect() + init_db()
з ідемпотентними CREATE TABLE IF NOT EXISTS.
"""
import sqlite3
import os
import json
import time
from contextlib import contextmanager

import config


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    with get_conn() as conn:
        c = conn.cursor()
        # Звички: назва + множина дат коли виконано (один рядок на виконання за день)
        c.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS habit_log (
                habit_id INTEGER NOT NULL,
                day TEXT NOT NULL,
                PRIMARY KEY (habit_id, day),
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
            )
        """)
        # Вакансії + pipeline пошуку роботи
        c.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                salary TEXT DEFAULT '',
                url TEXT DEFAULT '',
                source TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'new',
                notes TEXT DEFAULT '',
                added_at TEXT DEFAULT (date('now'))
            )
        """)
        # Міграція: source для старих БД де колонки ще немає
        try:
            c.execute("ALTER TABLE jobs ADD COLUMN source TEXT DEFAULT ''")
        except Exception:
            pass
        # Кеш зовнішніх API: ключ -> JSON + час запису
        c.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                cached_at REAL NOT NULL
            )
        """)


# --- Кеш-хелпери (щоб не довбати зовнішні API на кожен рефреш) ---

def cache_get(key: str, max_age_sec: int):
    """Повертає закешоване значення якщо свіже, інакше None."""
    with get_conn() as conn:
        row = conn.execute("SELECT value, cached_at FROM cache WHERE key = ?", (key,)).fetchone()
    if not row:
        return None
    if time.time() - row["cached_at"] > max_age_sec:
        return None
    try:
        return json.loads(row["value"])
    except json.JSONDecodeError:
        return None


def cache_set(key: str, value):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cache (key, value, cached_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, cached_at = excluded.cached_at",
            (key, json.dumps(value), time.time()),
        )
