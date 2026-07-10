from __future__ import annotations

from importlib import import_module

from flask import Flask


def register_blueprints(app: Flask) -> None:
    for module_name in (
        "home",
        "projects",
    ):
        module = import_module("apps.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def create_app(config: object) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)
    register_blueprints(app)
    return app
