"""Вкладка Віджети: погода, крипта, GitHub, календар, пошта."""
from flask import Blueprint, render_template

from auth import login_required
from sources import widgets_api, calendar_mail

widgets_bp = Blueprint("widgets", __name__, url_prefix="/widgets")


@widgets_bp.route("/")
@login_required
def index():
    return render_template(
        "tabs/widgets.html",
        weather=widgets_api.get_weather(),
        crypto=widgets_api.get_crypto(),
        github=widgets_api.get_github(),
        calendar=calendar_mail.get_calendar(),
        mail=calendar_mail.get_mail(),
    )
