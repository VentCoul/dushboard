"""Міст до Obsidian: читання/запис задач у markdown через git-клон віртуала.

Канонічне сховище задач — .md-файли віртуала. SQLite тут не задіяний.

Формат задачі — стандартний Obsidian/Markdown чекбокс:
    - [ ] незроблена задача
    - [x] зроблена задача

Кожна задача ідентифікується парою (відносний шлях файлу, номер рядка),
що кодується у task_id. Цього достатньо для toggle у межах одного pull-циклу.
"""
import os
import re
import glob

import config

# Рядок-чекбокс: відступ, маркер списку, [ ] або [x], текст
_TASK_RE = re.compile(r"^(?P<indent>\s*)[-*]\s+\[(?P<mark>[ xX])\]\s+(?P<text>.*)$")


def _git_repo():
    """Повертає git.Repo для віртуала або None якщо git недоступний/вимкнений."""
    if not config.VAULT_GIT_ENABLED:
        return None
    try:
        import git
        return git.Repo(config.VAULT_PATH)
    except Exception:
        return None


def pull():
    """git pull віртуала. Тихо ігнорує помилки (працюємо з тим що є локально)."""
    repo = _git_repo()
    if repo is None:
        return False
    try:
        repo.remotes.origin.pull()
        return True
    except Exception:
        return False


def _commit_push(rel_path: str, message: str):
    """Закомітити один файл і запушити. Повертає (ok, error_msg)."""
    repo = _git_repo()
    if repo is None:
        return True, None  # git вимкнено — просто лишаємо зміну локально
    try:
        repo.index.add([rel_path])
        repo.index.commit(message)
        repo.remotes.origin.push()
        return True, None
    except Exception as e:
        return False, str(e)


def _projects_root() -> str:
    return os.path.join(config.VAULT_PATH, config.VAULT_PROJECTS_DIR)


def vault_available() -> bool:
    return os.path.isdir(_projects_root())


def _encode_id(rel_path: str, lineno: int) -> str:
    # rel_path може містити '/', кодуємо через '::' + номер рядка
    return f"{rel_path}::{lineno}"


def _decode_id(task_id: str):
    rel_path, lineno = task_id.rsplit("::", 1)
    return rel_path, int(lineno)


def list_tasks(include_done: bool = False, do_pull: bool = True):
    """Зібрати задачі з усіх .md у папці проєктів.

    Повертає список dict: {id, text, done, project, file}.
    """
    if do_pull:
        pull()
    if not vault_available():
        return []

    tasks = []
    root = _projects_root()
    for path in sorted(glob.glob(os.path.join(root, "**", "*.md"), recursive=True)):
        rel_path = os.path.relpath(path, config.VAULT_PATH)
        project = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            m = _TASK_RE.match(line.rstrip("\n"))
            if not m:
                continue
            done = m.group("mark").lower() == "x"
            if done and not include_done:
                continue
            tasks.append({
                "id": _encode_id(rel_path, i),
                "text": m.group("text").strip(),
                "done": done,
                "project": project,
                "file": rel_path,
            })
    return tasks


def toggle_task(task_id: str):
    """Перемкнути [ ] <-> [x] у конкретному рядку. Повертає (ok, error)."""
    rel_path, lineno = _decode_id(task_id)
    abs_path = os.path.join(config.VAULT_PATH, rel_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        return False, str(e)
    if lineno >= len(lines):
        return False, "line out of range (віртуал змінився, онови сторінку)"

    m = _TASK_RE.match(lines[lineno].rstrip("\n"))
    if not m:
        return False, "рядок більше не є задачею (онови сторінку)"
    new_mark = " " if m.group("mark").lower() == "x" else "x"
    lines[lineno] = f"{m.group('indent')}- [{new_mark}] {m.group('text')}\n"

    with open(abs_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return _commit_push(rel_path, f"dushboard: toggle task in {rel_path}")


def add_task(project_file: str, text: str):
    """Додати нову задачу в кінець вказаного файлу проєкту. Повертає (ok, error)."""
    text = text.strip()
    if not text:
        return False, "порожній текст"
    abs_path = os.path.join(config.VAULT_PATH, project_file)
    if not os.path.isfile(abs_path):
        return False, "файл проєкту не знайдено"
    with open(abs_path, "a", encoding="utf-8") as f:
        f.write(f"\n- [ ] {text}\n")
    return _commit_push(project_file, f"dushboard: add task to {project_file}")


def list_project_files():
    """Список .md-файлів проєктів (відносні шляхи) для вибору куди додавати задачу."""
    if not vault_available():
        return []
    root = _projects_root()
    files = glob.glob(os.path.join(root, "**", "*.md"), recursive=True)
    return sorted(os.path.relpath(p, config.VAULT_PATH) for p in files)
