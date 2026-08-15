from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import render_template

from apps.resume import blueprint

_RESUME_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "resume.json"

logger = logging.getLogger(__name__)


def _load_resume() -> dict:
    try:
        return json.loads(_RESUME_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        logger.exception("Failed to load resume data from %s", _RESUME_PATH)
        return {}


_RESUME = _load_resume()


@blueprint.route("/")
def index():
    return render_template("resume/index.html", resume=_RESUME)