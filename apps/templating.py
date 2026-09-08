from __future__ import annotations

import datetime
from pathlib import Path

from jinja2 import ChoiceLoader, FileSystemLoader
from starlette.templating import Jinja2Templates

from apps.tags import tech_tag

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES_DIRS = [
    str(_PROJECT_ROOT / "apps" / "templates"),
    str(_PROJECT_ROOT / "apps" / "home" / "templates"),
    str(_PROJECT_ROOT / "apps" / "projects" / "templates"),
    str(_PROJECT_ROOT / "apps" / "resume" / "templates"),
]


def _url_for(name: str, **params) -> str:
    mapping = {
        "home_blueprint.index": "/",
        "home_blueprint.health": "/health",
        "projects_blueprint.index": "/projects/",
        "projects_blueprint.detail": f"/projects/info/{params.get('slug', '')}/",
        "resume_blueprint.index": "/resume/",
        "resume_blueprint.view": "/resume/view",
        "static": f"/static/{params.get('filename', '')}",
    }
    if name in mapping:
        base = mapping[name]
        # resume view may need query params
        if name == "resume_blueprint.view" and params:
            qs = "&".join(f"{k}={v}" for k, v in params.items() if k not in ("filename",))
            return f"{base}?{qs}" if qs else base
        return base
    return f"/{name}"


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


templates = Jinja2Templates(directory=_TEMPLATES_DIRS[0])
# Replace loader with ChoiceLoader covering all blueprint template dirs
templates.env.loader = ChoiceLoader([FileSystemLoader(d) for d in _TEMPLATES_DIRS])
templates.env.globals["tech_tag"] = tech_tag
templates.env.globals["url_for"] = _url_for
templates.env.globals["now"] = _now
