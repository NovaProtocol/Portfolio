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


# A field can mark the parts that may be hidden with `<redact>...</redact>`, and
# add a fallback label with `<redact-only>...</redact-only>`. The tags do not hide
# anything themselves: they only wrap the text in spans that the redaction toggle
# switches between. Marking is data, so a resume can change what it hides without
# a template edit.
_REDACT_RE = re.compile(r"<redact>(.*?)</redact>", re.DOTALL | re.IGNORECASE)
_REDACT_ONLY_RE = re.compile(
    r"<redact-only>(.*?)</redact-only>", re.DOTALL | re.IGNORECASE
)
_REDACT_TAG_RE = re.compile(
    r"<redact>(?P<real>.*?)</redact>"
    r"|<redact-only>(?P<alias>.*?)</redact-only>",
    re.DOTALL | re.IGNORECASE,
)


def _redact_markup(value) -> Markup:
    """Render a field's redaction tags as spans, escaping everything else.

    Escaped piece by piece rather than with Jinja's autoescape, because the tags
    have to survive as markup. Only the spans emitted here are trusted; their
    contents are escaped the same way as the text around them.
    """
    text = "" if value is None else str(value)
    parts: list[str] = []
    last = 0
    for match in _REDACT_TAG_RE.finditer(text):
        parts.append(str(escape(text[last:match.start()])))
        if match.group("real") is not None:
            parts.append(
                f'<span class="redactable">{escape(match.group("real"))}</span>'
            )
        else:
            parts.append(
                f'<span class="redact-only">{escape(match.group("alias"))}</span>'
            )
        last = match.end()
    parts.append(str(escape(text[last:])))
    return Markup("".join(parts))


def _strip_redact(value) -> str:
    """A field's real text, without the markup or the redacted-only fallback.

    Used for places that cannot carry markup (`href`) and for the project name
    that named resumes use as a key, so the fallback label must not become part
    of the identifier.
    """
    text = "" if value is None else str(value)
    text = _REDACT_ONLY_RE.sub("", text)
    return _REDACT_RE.sub(r"\1", text)


def _redact_marked(value) -> bool:
    """Whether a field carries a redaction marker.

    For values that cannot hold a span, such as an image path: the path is
    stripped for the attribute and the marker becomes a class instead. The
    fallback-only tag does not count, because it does not mark anything for
    covering.
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
