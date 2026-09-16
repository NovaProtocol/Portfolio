# Resume Blueprint

**Module:** `apps/routes/resume.py` — `APIRouter(prefix="/resume")`

Renders the resume from `data/resume.json`. Three themes, two printable pages, and a combined view.

## Routes

| Route | Handler | Query params | Description |
|-------|---------|--------------|-------------|
| `GET /resume/` | `apps.routes.resume.index` | — | Resume hub — renders `resume/index.html` |
| `GET /resume/view` | `apps.routes.resume.view` | `theme=1,2,3` (default 3), `page=1,2` (optional) | Single or combined page — `resume/view.html` (both pages) or `resume/page1.html` / `page2.html` for print |
| `GET /resume/qr.svg` | `apps.routes.resume.qr_svg` | — | Live portfolio QR — `image/svg+xml` via `segno`, `Cache-Control: public, max-age=86400`; 404 when `contact.access_code` is absent |

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

## Data — `data/resume.json`

- Single source of truth for name, contact, experience, education, skills, etc.
- `contact.portfolio` holds the plain base URL; `contact.access_code` is the single source of truth for the portfolio code. No `portfolio_label` field is authored — one helper (`_portfolio_links()` in `apps/routes/resume.py`) derives the magic link (`?access_code=`) and the display label, feeding both the templates and the QR endpoint so the printed link and QR payload cannot drift.
- Loaded **once at import**; a missing or malformed file is logged at `exception` level and falls back to `{}` so the app stays up (pages render empty rather than crashing).
- `page1.html` / `view.html` omit the portfolio line and QR block when the code is absent; `/resume/qr.svg` returns 404 in that case, never 500.
- Projects carry one shared `Source code available on request — repositories are private.` line (repos are private).
- No DB, no migrations — edit the JSON and reload.

## Route Registration

Router is `APIRouter(prefix="/resume")` and aggregated in `apps/routes/__init__.py`.

## Templates

| Template | Used when | Purpose |
|----------|-----------|---------|
| `resume/index.html` | `GET /resume/` | Hub / intro with link to `/view` |
| `resume/view.html` | `GET /resume/view` (no `page`) | Combined two-page document for print (both pages, chosen theme) |
| `resume/page1.html` | `GET /resume/view?page=1&theme=N` | Single page 1 (profile, experience top, etc.) |
| `resume/page2.html` | `GET /resume/view?page=2&theme=N` | Single page 2 (remaining sections) |
| `resume/_theme.html` | included by page1/page2/view | Theme styles (1, 2, 3) — colors, typography, print rules |

The print templates (`page1.html`, `page2.html`, `view.html`) are standalone documents — they do NOT extend `apps/templates/base.html` (only the `index.html` hub does). Theme selection is pure Jinja2 + CSS (no JS).

## Themes

- `theme=1, 2, 3` — validated; invalid values silently fall back to `3`.
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
- Portfolio QR is served live at `GET /resume/qr.svg` (SVG via `segno`); no static QR image is committed.
- No additional JS for the resume — pure FastAPI + Jinja2 + CSS for reliable printing.

## Crawler Discouragement

- `GET /robots.txt` returns `User-agent: *` + `Disallow: /` as `text/plain`.
- Primary noindex signal is the `X-Robots-Tag: noindex, nofollow` header set at the site-block level in `caddy/Caddyfile`, so it covers app routes, `/static` assets, and the separately-containerised documentation service. The resume print templates do not extend `base.html`, so the `<meta name="robots">` tag there is defence-in-depth for `base.html` pages only.
