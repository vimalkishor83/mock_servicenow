import logging
import os
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, g, request, send_from_directory

import config
from models.db_models import Incident, db
from routes.auth_routes import auth_blueprint
from routes.incident_routes import incident_blueprint
from routes.kb_routes import kb_blueprint
from routes.ui_routes import ui_blueprint
from routes.user_routes import user_blueprint
from swagger.swagger_config import register_swagger



def create_app(start_background_jobs=True):
    app = Flask(__name__)
    # Behind a reverse proxy under a path prefix (Caddy sets X-Forwarded-Prefix). No effect when served at root.
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.config.from_object(config)
    configure_logging(app)

    Path(app.config["LOG_FILE"]).parent.mkdir(parents=True, exist_ok=True)
    Path(config.BASE_DIR / "database").mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(incident_blueprint)
    app.register_blueprint(kb_blueprint)
    app.register_blueprint(ui_blueprint)
    app.register_blueprint(user_blueprint)
    register_swagger(app)
    register_request_logging(app)

    # Shared, pre-built library files (Bootstrap), bind-mounted read-only at
    # /common-static from the host's /home/claudedev/office/common-static --
    # one copy shared across office apps instead of each app vendoring its own.
    common_static_dir = os.environ.get("COMMON_STATIC_DIR", "/common-static")

    @app.route("/common-static/<path:filename>")
    def common_static(filename):
        return send_from_directory(common_static_dir, filename)

    with app.app_context():
        db.create_all()
        seed_database_if_needed(app)

    if start_background_jobs and app.config.get("ENABLE_SCHEDULER", True):
        start_scheduler(app)

    return app


def configure_logging(app):
    log_path = Path(config.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
        encoding='utf-8',
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s  %(levelname)-8s  %(name)s  %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    ))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not root.handlers:
        root.addHandler(handler)

    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    app.logger.setLevel(logging.INFO)


def register_request_logging(app):
    @app.before_request
    def before_request():
        g.started_at = time.perf_counter()

    @app.after_request
    def after_request(response):
        elapsed_ms = (time.perf_counter() - g.get("started_at", time.perf_counter())) * 1000
        app.logger.info(
            "method=%s path=%s query=%s status=%s duration_ms=%.2f remote_addr=%s",
            request.method,
            request.path,
            request.query_string.decode("utf-8"),
            response.status_code,
            elapsed_ms,
            request.headers.get("X-Forwarded-For", request.remote_addr),
        )
        return response



def seed_database_if_needed(app):
    from scripts.generate_dummy_data import (
        ensure_admin, seed_groups, seed_incidents, seed_kb_articles, seed_users,
    )

    ensure_admin()
    if (
        app.config.get("AUTO_SEED_DUMMY_DATA", True)
        and Incident.query.count() < app.config["DUMMY_INCIDENT_COUNT"]
    ):
        app.logger.info("Seeding dummy ServiceNow data")
        seed_groups(app.config["DUMMY_GROUP_COUNT"])
        seed_users(app.config["DUMMY_USER_COUNT"])
        seed_incidents(app.config["DUMMY_INCIDENT_COUNT"])

    # Always seed KB articles if not already present (idempotent)
    seed_kb_articles()


def start_scheduler(app):
    if getattr(app, "_mock_snow_scheduler_started", False):
        return
    app._mock_snow_scheduler_started = True

    from services.incident_service import IncidentService

    def run():
        with app.app_context():
            while True:
                time.sleep(app.config["SCHEDULER_INTERVAL_SECONDS"])
                for _ in range(app.config["SCHEDULER_INCIDENTS_PER_RUN"]):
                    IncidentService.create_random_incident()
                app.logger.info(
                    "Generated %s scheduled incidents",
                    app.config["SCHEDULER_INCIDENTS_PER_RUN"],
                )

    thread = threading.Thread(target=run, name="mock-snow-scheduler", daemon=True)
    thread.start()


app = create_app(start_background_jobs=os.getenv("WERKZEUG_RUN_MAIN") != "true")


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=True)
