"""Вкладка пошуку роботи: список вакансій з pipeline-статусами."""
from flask import Blueprint, render_template, request, redirect, url_for

from auth import login_required
from sources.jobs import (
    list_jobs, add_job, set_status, delete_job,
    counts_by_status, import_from_bot,
    STATUSES, STATUS_MAP, STATUS_CSS, STATUS_KEYS,
)

jobs_bp = Blueprint("jobs", __name__, url_prefix="/jobs")


def _ctx():
    return dict(statuses=STATUSES, status_map=STATUS_MAP, status_css=STATUS_CSS)


@jobs_bp.route("/")
@login_required
def index():
    active = request.args.get("status", "")
    return render_template(
        "tabs/jobs.html",
        jobs=list_jobs(active or None),
        counts=counts_by_status(),
        active_status=active,
        **_ctx(),
    )


@jobs_bp.route("/add", methods=["POST"])
@login_required
def add():
    add_job(
        request.form.get("title", ""),
        request.form.get("company", ""),
        request.form.get("salary", ""),
        request.form.get("url", ""),
    )
    return redirect(url_for("jobs.index"))


@jobs_bp.route("/status", methods=["POST"])
@login_required
def change_status():
    set_status(int(request.form["id"]), request.form["status"])
    active = request.form.get("active_status", "")
    return render_template(
        "tabs/_jobs_list.html",
        jobs=list_jobs(active or None),
        counts=counts_by_status(),
        active_status=active,
        **_ctx(),
    )


@jobs_bp.route("/import", methods=["POST"])
@login_required
def bot_import():
    added = import_from_bot()
    active = request.args.get("status", "")
    return render_template(
        "tabs/jobs.html",
        jobs=list_jobs(active or None),
        counts=counts_by_status(),
        active_status=active,
        import_result=added,
        **_ctx(),
    )


@jobs_bp.route("/delete", methods=["POST"])
@login_required
def delete():
    delete_job(int(request.form["id"]))
    active = request.form.get("active_status", "")
    return render_template(
        "tabs/_jobs_list.html",
        jobs=list_jobs(active or None),
        counts=counts_by_status(),
        active_status=active,
        **_ctx(),
    )
