from __future__ import annotations

import json
from pathlib import Path

from flask import render_template

from apps.resume import blueprint

_RESUME_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "resume.json"


@blueprint.route("/")
def index():
    resume = json.loads(_RESUME_PATH.read_text())
    return render_template("resume/index.html", resume=resume)
