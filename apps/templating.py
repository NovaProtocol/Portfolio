from __future__ import annotations

import datetime
import re
from pathlib import Path

from jinja2 import ChoiceLoader, FileSystemLoader
from markupsafe import Markup, escape
from starlette.templating import Jinja2Templates

from apps.config import get_config
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


# A field can mark the parts that may be hidden with `<redact>...</redact>`.
# The tags do not hide anything themselves: they only wrap the text in a span
# that the redaction toggle covers on screen and in print. Marking is data, so a
# resume can change what it hides without a template edit.
_REDACT_RE = re.compile(r"<redact>(.*?)</redact>", re.DOTALL | re.IGNORECASE)


def _redact_markup(value) -> Markup:
    """Render a field's `<redact>` tags as spans, escaping everything else.

    Escaped piece by piece rather than with Jinja's autoescape, because the tag
    has to survive as markup. Only the span emitted here is trusted; the content
    inside it is escaped the same way as the text around it.
    """
    text = "" if value is None else str(value)
    parts: list[str] = []
    last = 0
    for match in _REDACT_RE.finditer(text):
        parts.append(str(escape(text[last:match.start()])))
        parts.append(f'<span class="redactable">{escape(match.group(1))}</span>')
        last = match.end()
    parts.append(str(escape(text[last:])))
    return Markup("".join(parts))


def _strip_redact(value) -> str:
    """A field's plain text, for places that cannot carry markup, such as href."""
    return _REDACT_RE.sub(r"\1", "" if value is None else str(value))


def _redact_marked(value) -> bool:
    """Whether a field carries a redaction marker.

    For values that cannot hold a span, such as an image path: the path is
    stripped for the attribute and the marker becomes a class instead.
    """
    return bool(value) and bool(_REDACT_RE.search(str(value)))


templates = Jinja2Templates(directory=_TEMPLATES_DIRS[0])
# Replace loader with ChoiceLoader covering all blueprint template dirs
templates.env.loader = ChoiceLoader([FileSystemLoader(d) for d in _TEMPLATES_DIRS])
templates.env.globals["tech_tag"] = tech_tag
templates.env.globals["url_for"] = _url_for
templates.env.globals["now"] = _now
templates.env.globals["contact_email"] = get_config().CONTACT_EMAIL
templates.env.filters["redact"] = _redact_markup
templates.env.filters["strip_redact"] = _strip_redact
templates.env.filters["redact_marked"] = _redact_marked
