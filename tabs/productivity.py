"""Вкладка Продуктивність: задачі/проєкти з Obsidian + звички з SQLite."""
import datetime

from flask import Blueprint, render_template, request

from auth import login_required
from db import get_conn
from sources import obsidian

productivity_bp = Blueprint("productivity", __name__)


# --- Звички (SQLite) ---

def _today():
    return datetime.date.today().isoformat()


def _habits_today():
    today = _today()
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT h.id, h.name,
                   EXISTS(SELECT 1 FROM habit_log l WHERE l.habit_id = h.id AND l.day = ?) AS done
            FROM habits h ORDER BY h.id
        """, (today,)).fetchall()
    return [dict(r) for r in rows]


@productivity_bp.route("/")
@login_required
def index():
    return render_template(
        "tabs/productivity.html",
        tasks=obsidian.list_tasks(),
        vault_ok=obsidian.vault_available(),
        project_files=obsidian.list_project_files(),
        habits=_habits_today(),
    )


# --- HTMX partial-роути (повертають шматок HTML) ---

@productivity_bp.route("/tasks/partial")
@login_required
def tasks_partial():
    return render_template(
        "tabs/_tasks.html",
        tasks=obsidian.list_tasks(),
        vault_ok=obsidian.vault_available(),
    )


@productivity_bp.route("/tasks/toggle", methods=["POST"])
@login_required
def task_toggle():
    ok, err = obsidian.toggle_task(request.form["id"])
    return render_template(
        "tabs/_tasks.html",
        tasks=obsidian.list_tasks(do_pull=False),
        vault_ok=obsidian.vault_available(),
        error=None if ok else err,
    )


@productivity_bp.route("/tasks/add", methods=["POST"])
@login_required
def task_add():
    ok, err = obsidian.add_task(request.form["file"], request.form.get("text", ""))
    return render_template(
        "tabs/_tasks.html",
        tasks=obsidian.list_tasks(do_pull=False),
        vault_ok=obsidian.vault_available(),
        error=None if ok else err,
    )


@productivity_bp.route("/habits/toggle", methods=["POST"])
@login_required
def habit_toggle():
    habit_id = int(request.form["id"])
    today = _today()
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM habit_log WHERE habit_id = ? AND day = ?", (habit_id, today)
        ).fetchone()
        if exists:
            conn.execute("DELETE FROM habit_log WHERE habit_id = ? AND day = ?", (habit_id, today))
        else:
            conn.execute("INSERT INTO habit_log (habit_id, day) VALUES (?, ?)", (habit_id, today))
    return render_template("tabs/_habits.html", habits=_habits_today())


@productivity_bp.route("/habits/add", methods=["POST"])
@login_required
def habit_add():
    name = request.form.get("name", "").strip()
    if name:
        with get_conn() as conn:
            conn.execute("INSERT INTO habits (name) VALUES (?)", (name,))
    return render_template("tabs/_habits.html", habits=_habits_today())
