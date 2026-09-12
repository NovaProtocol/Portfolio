# Projects Blueprint

**Module:** `apps/routes/projects.py` — `APIRouter(prefix="/projects")`

Project catalog — listing, detail pages, and the data shape that drives them.

## Routes

| Route | Handler | Description |
|-------|---------|-------------|
| `GET /projects/` | `apps.routes.projects.index` | Listing — renders `projects/index.html` with active projects |
| `GET /projects/info/{slug}/` | `apps.routes.projects.detail` | Detail — renders `projects/detail.html` for `PROJECTS[slug]` or `404` |

```python
# apps/routes/projects.py (trimmed)
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from apps.data import PROJECTS
from apps.templating import templates

router = APIRouter(prefix="/projects")

def ordered_projects() -> list[tuple[str, dict]]:
 return [(slug, p) for slug, p in PROJECTS.items() if p.get("active")]

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
 return templates.TemplateResponse(request, "projects/index.html", {"projects": ordered_projects()})

@router.get("/info/{slug}/", response_class=HTMLResponse)
async def detail(request: Request, slug: str):
 project = PROJECTS.get(slug)
 if not project:
 raise HTTPException(status_code=404, detail="Project not found")
 return templates.TemplateResponse(request, "projects/detail.html", {"project": project, "slug": slug})
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

## Data Source

`apps/data.py:PROJECTS` is the single source of truth; routes import it. Templates are namespaced `templates/projects/{index,detail,_card}.html` but resolved by the Jinja2 `templates` object from `apps/templating.py`.

## Templates

- `apps/projects/templates/projects/index.html` — loops `projects` from `ordered_projects()`, includes `_card.html` partial per entry.
- `apps/projects/templates/projects/detail.html` — title, subtitle, description paragraphs, tech tags (via `apps/tags. tech_tag`), features, status, live embed (`url`), and `links` / `buttons`.
- `apps/templates/base.html` is the parent for both — all routes extend it so layout, nav, and footer are consistent.

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
