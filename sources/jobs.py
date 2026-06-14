"""CRUD для вакансій + pipeline + імпорт з job-hunter бота."""
import sqlite3
import os

from db import get_conn
import config

STATUSES = [
    ("new",       "Нові",         "apple-badge-gray"),
    ("applied",   "Відгукнувся",  "apple-badge-blue"),
    ("hr_call",   "HR-дзвінок",   "apple-badge-purple"),
    ("technical", "Технічне",     "apple-badge-orange"),
    ("offer",     "Офер",         "apple-badge-green"),
    ("rejected",  "Відмова",      "apple-badge-red"),
]

STATUS_KEYS = [s[0] for s in STATUSES]
STATUS_MAP  = {s[0]: s[1] for s in STATUSES}
STATUS_CSS  = {s[0]: s[2] for s in STATUSES}

SITE_LABELS = {"djinni": "Djinni", "workua": "Work.ua", "dou": "DOU"}


def list_jobs(status=None):
    sql = "SELECT * FROM jobs"
    args = ()
    if status:
        sql += " WHERE status = ?"
        args = (status,)
    sql += " ORDER BY added_at DESC, id DESC"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def add_job(title, company, salary="", url="", source="", notes=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO jobs (title, company, salary, url, source, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title.strip(), company.strip(), salary.strip(), url.strip(), source, notes.strip()),
        )


def set_status(job_id: int, status: str):
    if status not in STATUS_KEYS:
        return
    with get_conn() as conn:
        conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))


def delete_job(job_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))


def counts_by_status():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status"
        ).fetchall()
    return {r["status"]: r["cnt"] for r in rows}


def import_from_bot(limit=50):
    """Імпортувати нові вакансії з job-hunter БД (уникає дублів по URL).

    Повертає кількість доданих вакансій або -1 якщо БД недоступна.
    """
    db_path = config.JOB_HUNTER_DB
    if not db_path or not os.path.isfile(db_path):
        return -1

    try:
        src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        src.row_factory = sqlite3.Row
        rows = src.execute(
            "SELECT title, company, salary, url, site FROM vacancies "
            "ORDER BY found_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        src.close()
    except Exception:
        return -1

    added = 0
    with get_conn() as conn:
        existing_urls = {r[0] for r in conn.execute("SELECT url FROM jobs").fetchall()}
        for r in rows:
            if r["url"] in existing_urls:
                continue
            source = SITE_LABELS.get(r["site"], r["site"] or "")
            conn.execute(
                "INSERT INTO jobs (title, company, salary, url, source, status) "
                "VALUES (?, ?, ?, ?, ?, 'new')",
                (
                    (r["title"] or "").strip(),
                    (r["company"] or "").strip(),
                    (r["salary"] or "").strip(),
                    (r["url"] or "").strip(),
                    source,
                ),
            )
            added += 1
    return added
