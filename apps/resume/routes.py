from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import abort, render_template, request

from apps.resume import blueprint

_RESUME_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "resume.json"

logger = logging.getLogger(__name__)


def _load_resume() -> dict:
    try:
        return json.loads(_RESUME_PATH.read_text())  # type: ignore[no-any-return]
    except (OSError, json.JSONDecodeError):
        logger.exception("Failed to load resume data from %s", _RESUME_PATH)
        return {}


_RESUME = _load_resume()

_THEMES = {1, 2, 3}


@blueprint.route("/")
def index():
    return render_template("resume/index.html", resume=_RESUME)


@blueprint.route("/view")
def view():
    """Single or combined resume page, themeable.

    Query params:
      page  - 1 or 2 for a single page, omitted for the combined
              two-page document used in printing.
      theme - 1, 2, or 3 (defaults to 3).
    """
    theme = request.args.get("theme", type=int, default=3)
    if theme not in _THEMES:
        theme = 3

    page = request.args.get("page", type=int)
    if page is not None:
        template = {1: "resume/page1.html", 2: "resume/page2.html"}.get(page)
        if not template:
            abort(404)
        return render_template(template, resume=_RESUME, theme=theme)

    return render_template("resume/view.html", resume=_RESUME, theme=theme)
