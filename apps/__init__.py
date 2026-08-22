from __future__ import annotations

from importlib import import_module
from pathlib import Path

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from apps import tags


def register_blueprints(app: Flask) -> None:
    for module_name in (
        "home",
        "projects",
        "resume",
    ):
        module = import_module(f"apps.{module_name}.routes")
        app.register_blueprint(module.blueprint)


def create_app(config: object) -> Flask:
    static_dir = Path(__file__).resolve().parent.parent / "static"
    app = Flask(__name__, static_folder=str(static_dir), static_url_path="/static")
    app.config.from_object(config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    tags.init_app(app)
    register_blueprints(app)

    return app
