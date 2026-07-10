from __future__ import annotations

from apps.home import blueprint


@blueprint.route("/")
def hello():
    return "<h1>Hello World</h1>"
