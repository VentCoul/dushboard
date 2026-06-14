"""Простий сесійний логін: один пароль з .env, cookie-сесія Flask.

Тільки для себе — без таблиці юзерів, без реєстрації.
"""
from functools import wraps
from flask import Blueprint, request, session, redirect, url_for, render_template, flash

import config

auth_bp = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("productivity.index"))
    if request.method == "POST":
        if request.form.get("password") == config.DASHBOARD_PASSWORD:
            session["logged_in"] = True
            session.permanent = True
            return redirect(request.args.get("next") or url_for("productivity.index"))
        flash("Невірний пароль")
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
