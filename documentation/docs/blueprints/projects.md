# Projects Blueprint

**Module:** `apps/projects/` — `projects_blueprint`, `url_prefix="/projects"`

Project catalog — listing, detail pages, and the data shape that drives them.

## Routes

| Route | Handler | Description |
|-------|---------|-------------|
| `GET /projects/` | `apps.projects.routes.index` | Listing — renders `projects/index.html` with active projects |
| `GET /projects/info/<slug>/` | `apps.projects.routes.detail` | Detail — renders `projects/detail.html` for `PROJECTS[slug]` or `404` |

```python
# apps/projects/routes.py (trimmed)
from __future__ import annotations

from flask import abort, render_template

from apps.projects import blueprint

PROJECTS: dict[str, dict] = {
    "gatekeeper": {"title": "GateKeeper", ...},
    "portfolio":  {"title": "Portfolio", ...},
    "water-billing-system": {"title": "Water Billing System", ...},
    # buddys-freelance-project (active=false), novaprotocol, solvelspace (halted), mle-review
}

def ordered_projects() -> list[tuple[str, dict]]:
    return [(slug, p) for slug, p in PROJECTS.items() if p.get("active")]

@blueprint.route("/")
def index():
    return render_template("projects/index.html", projects=ordered_projects())

@blueprint.route("/info/<slug>/")
def detail(slug: str):
    project = PROJECTS.get(slug)
    if not project:
        abort(404)
    return render_template("projects/detail.html", project=project, slug=slug)
```

## Data Shape

Add a new project by inserting an entry into `PROJECTS` (see README and Getting Started):

| Field | Required | Description |
|-------|----------|-------------|
| `title` | yes | Display name |
| `subtitle` | yes | Client / context |
| `description` | yes | 2–3 sentence summary (list of paragraphs) |
| `tech` | yes | `{web: [...], mobile: [...]}` tag lists |
| `features` | no | Bullet list of key features |
| `status` | no | `operational` / `in progress` / `halted` |
| `note` | no | Short note under the status tag |
| `status_reason` | no | Long reason for `halted` |
| `url` | no | Live site URL (embed with online/offline check) |
| `github` | no | Source repo link |
| `image` | no | Path relative to `static/` (detail page) |
| `links` | no | `[{name, url, icon}]` external links |
| `buttons` | no | Action buttons |
| `active` | yes | `true` → appears in listing |

Place preview images at `static/assets/images/<slug>/preview.png` and reference them via `image:`.

`reason:` (freeform) explains *why* the project exists — shown on detail pages as context.

## Blueprint Definition

```python
# apps/projects/__init__.py
from flask import Blueprint

blueprint = Blueprint(
    "projects_blueprint",
    __name__,
    url_prefix="/projects",
    template_folder="templates",
)
```

Templates are namespaced `templates/projects/{index,detail,_card}.html` but resolved by the Flask template search that includes the shared `apps/templates/`.

## Templates

- `apps/projects/templates/projects/index.html` — loops `projects` from `ordered_projects()`, includes `_card.html` partial per entry.
- `apps/projects/templates/projects/detail.html` — title, subtitle, description paragraphs, tech tags (via `apps/tags. tech_tag`), features, status, live embed (`url`), and `links` / `buttons`.
- `apps/templates/base.html` is the parent for both — all blueprints extend it so layout, nav, and footer are consistent.

## Embeds & Links

- `url:` is rendered as a live iframe/embed on detail pages with an online/offline indicator (checked client-side).
- `links:` render as `a` tags with FontAwesome icons (`icon:` is the FA class).
- Only `active: true` projects appear in `ordered_projects()` and on the home page highlights.

## Example Entry

```python
"my-project": {
    "active": True,
    "title": "My Project",
    "subtitle": "Client or context",
    "description": ["What it does, who it's for.", "Why it was built."],
    "tech": {"web": ["Flask", "Docker"]},
    "features": ["Feature one", "Feature two"],
    "url": "https://my-project.example.com",
    "github": "https://github.com/you/my-project",
    "image": "assets/images/my-project/preview.png",
    "links": [
        {"name": "Admin Panel", "url": "https://my-project.example.com/admin", "icon": "fas fa-shield-alt"},
    ],
    "buttons": [],
}
```
