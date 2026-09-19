# Resume Blueprint

**Module:** `apps/routes/resume.py` using `APIRouter(prefix="/resume")`

Renders the resume from `data/resume.json`. Three themes, two printable pages, and a combined view.

## Routes

| Route | Handler | Query params | Description |
|-------|---------|--------------|-------------|
| `GET /resume/` | `apps.routes.resume.index` | n/a | Resume hub rendering `resume/index.html` |
| `GET /resume/view` | `apps.routes.resume.view` | `theme=1,2,3` (default 3), `page=1,2` (optional) | Single or combined page using `resume/view.html` (both pages) or `resume/page1.html` / `page2.html` for print |

```python
# apps/routes/resume.py (trimmed)
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from apps.templating import templates

router = APIRouter(prefix="/resume")

_RESUME = _load_resume()
_THEMES = {1, 2, 3}

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
 return templates.TemplateResponse(request, "resume/index.html", {"resume": _RESUME})

@router.get("/view", response_class=HTMLResponse)
async def view(request: Request, page: int | None = None, theme: int = 3):
 if theme not in _THEMES:
 theme = 3
 if page is not None:
 mapping = {1: "resume/page1.html", 2: "resume/page2.html"}
 template = mapping.get(page)
 if not template:
 raise HTTPException(status_code=404, detail="Not found")
 return templates.TemplateResponse(request, template, {"resume": _RESUME, "theme": theme})
 return templates.TemplateResponse(request, "resume/view.html", {"resume": _RESUME, "theme": theme})
```

## Data in `data/resume.json`

- Single source of truth for name, contact, experience, education, skills, etc.
- `contact.portfolio` holds the plain base URL for the site. It is not printed on the resume: the header carries the LinkedIn and GitHub links, which a reader can follow without a code.
- Loaded **once at import**. A missing or malformed file is logged at `exception` level and falls back to `{}` so the app stays up (pages render empty rather than crashing).
- Optional keys render only when present (`{% if %}` guarded), so a project or school entry that omits them looks exactly as it did before they existed:
  - `education[].status` — a short line under the degree (for example a graduation status).
  - `projects[].status_line` — a build-state line directly under the tech stack, above `highlights`, styled with `.demo-line`.
- Projects carry one shared `Live demos of selected projects are hosted on my portfolio. Source code is available on request. Repositories are private.` line (repos are private).
- A project with a live demo carries a `url` in `resume.json`, rendering a `Live demo: <url>` line under its tech stack. Projects without one (SolveSpace, halted) omit it via the `{% if proj.url %}` guard.
- No DB and no migrations. Edit the JSON and reload.

## Route Registration

Router is `APIRouter(prefix="/resume")` and aggregated in `apps/routes/__init__.py`.

## Templates

| Template | Used when | Purpose |
|----------|-----------|---------|
| `resume/index.html` | `GET /resume/` | Hub / intro with link to `/view` |
| `resume/view.html` | `GET /resume/view` (no `page`) | Combined two-page document for print (both pages, chosen theme) |
| `resume/page1.html` | `GET /resume/view?page=1&theme=N` | Single page 1 (profile, experience top, etc.) |
| `resume/page2.html` | `GET /resume/view?page=2&theme=N` | Single page 2 (remaining sections) |
| `resume/_theme.html` | included by page1/page2/view | Theme styles (1, 2, 3) for colors, typography, and print rules |

The print templates (`page1.html`, `page2.html`, `view.html`) are standalone documents. They do NOT extend `apps/templates/base.html` (only the `index.html` hub does). Theme selection is pure Jinja2 + CSS (no JS).

## Themes

- `theme=1, 2, 3` is validated. Invalid values silently fall back to `3`.
- Each theme has its own CSS variables and layout tweaks (accent color, font weight, spacing) so the same content can be rendered in three visual treatments.
- Print: use the combined `view.html` (no `page` param) → browser print → two pages.

## URLs

```
/resume/ → hub
/resume/view → combined, theme 3 (default)
/resume/view?theme=1 → combined, theme 1
/resume/view?page=1 → page 1 only, theme 3
/resume/view?page=2&theme=2 → page 2 only, theme 2
/resume/view?page=3 → 404 (only 1 and 2 exist)
```

## Static Assets

- Portrait photo: `static/assets/images/resume_image.JPG`
- No additional JS for the resume. It is pure FastAPI + Jinja2 + CSS for reliable printing.

## Metric Note

The thesis entry cites `86.96% validation accuracy`. That figure is validation accuracy on the thesis author's reference dataset — a single authored split, not a benchmark protocol or a cross-dataset comparison. It is reported as measured, and it is not comparable with published signature-verification benchmarks.

`<FILL: dataset size / split>`

## Crawler Discouragement

- `/robots.txt` is **no longer an app route**: GateKeeper serves it from a custom page, so the file is answered before the request reaches this app. The body is unchanged (`User-agent: *` + `Disallow: /`).
- Primary noindex signal is the `X-Robots-Tag: noindex, nofollow` header set at the site-block level in `caddy/Caddyfile`, so it covers app routes, `/static` assets, and the separately-containerised documentation service. The resume print templates do not extend `base.html`, so the `<meta name="robots">` tag there is defence-in-depth for `base.html` pages only.
