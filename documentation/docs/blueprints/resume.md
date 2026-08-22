# Resume Blueprint

**Module:** `apps/resume/` — `resume_blueprint`, `url_prefix="/resume"`

Renders the resume from `data/resume.json`. Three themes, two printable pages, and a combined view.

## Routes

| Route | Handler | Query params | Description |
|-------|---------|--------------|-------------|
| `GET /resume/` | `apps.resume.routes.index` | — | Resume hub — renders `resume/index.html` |
| `GET /resume/view` | `apps.resume.routes.view` | `theme=1,2,3` (default 3), `page=1,2` (optional) | Single or combined page — `resume/view.html` (both pages) or `resume/page1.html` / `page2.html` for print |

```python
# apps/resume/routes.py (trimmed)
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
        return json.loads(_RESUME_PATH.read_text())
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
```

## Data — `data/resume.json`

- Single source of truth for name, contact, experience, education, skills, etc.
- Loaded **once at import**; a missing or malformed file is logged at `exception` level and falls back to `{}` so the app stays up (pages render empty rather than crashing).
- No DB, no migrations — edit the JSON and reload.

## Blueprint Definition

```python
# apps/resume/__init__.py
from flask import Blueprint

blueprint = Blueprint(
    "resume_blueprint",
    __name__,
    url_prefix="/resume",
    template_folder="templates",
)
```

## Templates

| Template | Used when | Purpose |
|----------|-----------|---------|
| `resume/index.html` | `GET /resume/` | Hub / intro with link to `/view` |
| `resume/view.html` | `GET /resume/view` (no `page`) | Combined two-page document for print (both pages, chosen theme) |
| `resume/page1.html` | `GET /resume/view?page=1&theme=N` | Single page 1 (profile, experience top, etc.) |
| `resume/page2.html` | `GET /resume/view?page=2&theme=N` | Single page 2 (remaining sections) |
| `resume/_theme.html` | included by page1/page2/view | Theme styles (1, 2, 3) — colors, typography, print rules |

All extend `apps/templates/base.html` via the shared template folder. Theme selection is pure Jinja2 + CSS (no JS).

## Themes

- `theme=1, 2, 3` — validated; invalid values silently fall back to `3`.
- Each theme has its own CSS variables and layout tweaks (accent color, font weight, spacing) so the same content can be rendered in three visual treatments.
- Print: use the combined `view.html` (no `page` param) → browser print → two pages.

## URLs

```
/resume/                        → hub
/resume/view                    → combined, theme 3 (default)
/resume/view?theme=1            → combined, theme 1
/resume/view?page=1             → page 1 only, theme 3
/resume/view?page=2&theme=2     → page 2 only, theme 2
/resume/view?page=3             → 404 (only 1 and 2 exist)
```

## Static Assets

- Portrait photo: `static/assets/images/resume_image.JPG`
- No additional JS for the resume — pure Flask + Jinja2 + CSS for reliable printing.
