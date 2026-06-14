"""Точка входу дашборда: створення Flask-app, реєстрація blueprints."""
import datetime

from flask import Flask

import config
from db import init_db
from auth import auth_bp
from tabs.productivity import productivity_bp
from tabs.widgets import widgets_bp
from tabs.monitoring import monitoring_bp
from tabs.ai import ai_bp
from tabs.jobs import jobs_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=30)

    init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(productivity_bp)  # "/" — головна вкладка
    app.register_blueprint(widgets_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(jobs_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
