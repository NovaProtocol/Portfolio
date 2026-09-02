from __future__ import annotations

from importlib import import_module
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from apps import tags

_ERROR_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}

def _error_response(code: int, title: str, message: str):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({"error": title, "code": code}), code
    return render_template("errors/error.html", code=code, title=title, message=message), code


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

    @app.after_request
    def _csp_frame_src(resp):
        # Allow GateKeeper iframe on portfolio detail page (same-apex)
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; connect-src 'self'; "
            "frame-src 'self' https://*.projectnova.download; "
            "frame-ancestors 'self' https://*.projectnova.download"
        )
        return resp

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    tags.init_app(app)
    register_blueprints(app)

    @app.errorhandler(HTTPException)
    def _handle_http(e: HTTPException):
        code = e.code or 500
        title = _ERROR_TITLES.get(code, e.name or "Error")
        msg = e.description if code != 404 else "The page you're looking for doesn't exist."
        if code not in _ERROR_TITLES:
            code = 500
            title = "Internal Server Error"
            msg = "Something went wrong."
        return _error_response(code, title, msg)

    @app.errorhandler(Exception)
    def _handle_exc(e: Exception):
        if isinstance(e, HTTPException):
            return _handle_http(e)
        return _error_response(500, "Internal Server Error", "Something went wrong.")

    return app
