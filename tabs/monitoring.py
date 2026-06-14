"""Вкладка Моніторинг: метрики VPS + статус Telegram-ботів."""
from flask import Blueprint, render_template

from auth import login_required
from sources import bots

monitoring_bp = Blueprint("monitoring", __name__, url_prefix="/monitoring")


@monitoring_bp.route("/")
@login_required
def index():
    return render_template(
        "tabs/monitoring.html",
        metrics=bots.vps_metrics(),
        statuses=bots.bot_statuses(),
    )


@monitoring_bp.route("/partial")
@login_required
def partial():
    """HTMX авто-оновлення блоку метрик."""
    return render_template(
        "tabs/_monitoring.html",
        metrics=bots.vps_metrics(),
        statuses=bots.bot_statuses(),
    )
