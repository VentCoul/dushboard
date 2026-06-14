"""Вкладка AI — заглушка. Blueprint уже на місці, щоб додати модель пізніше."""
from flask import Blueprint, render_template

from auth import login_required

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")


@ai_bp.route("/")
@login_required
def index():
    return render_template("tabs/ai.html")
