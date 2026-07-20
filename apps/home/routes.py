from __future__ import annotations

from flask import jsonify, render_template

from apps.home import blueprint


@blueprint.route("/")
def index():
    return render_template("home/index.html")


@blueprint.route("/health")
def health():
    return jsonify({"status": "ok"})
