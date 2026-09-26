# Resume Blueprint

**Module:** `apps/routes/resume.py` using `APIRouter(prefix="/resume")`

Renders the resume from `data/resume.json`. One visual theme, two printable pages, a
combined view, and **two variants**: a mechanical-first running order and a
software-first one, over the same content.

## Routes

| Route | Handler | Query params | Description |
|-------|---------|--------------|-------------|
| `GET /resume/` | `apps.routes.resume.index` | `variant=mechanical,software` (default `mechanical`) | Resume hub rendering `resume/index.html`, with the variant selector |
| `GET /resume/view` | `apps.routes.resume.view` | `variant=mechanical,software`, `page=1,2` (optional) | Single or combined page using `resume/view.html` (both pages) or `resume/page1.html` / `page2.html` for print |

```python
# apps/routes/resume.py (trimmed)
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from apps.templating import templates

router = APIRouter(prefix="/resume")

_RESUME = _load_resume()
DEFAULT_VARIANT = "mechanical"

def _order_projects(resume: dict, variant: str) -> dict:
    """The resume with `projects` in the order that variant asks for."""
    spec = (resume.get("variants") or {}).get(variant) or {}
    order = spec.get("order")
    if not order:
        return resume
    by_name = {p.get("name"): p for p in resume.get("projects") or []}
    chosen = [by_name[name] for name in order if name in by_name]
    return {**resume, "projects": chosen}

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, variant: str = DEFAULT_VARIANT):
    return templates.TemplateResponse(
        request, "resume/index.html", _resume_context(_normalise_variant(variant)))

@router.get("/view", response_class=HTMLResponse)
async def view(request: Request, page: int | None = None, variant: str = DEFAULT_VARIANT):
    resolved = _normalise_variant(variant)
    if page is not None:
        mapping = {1: "resume/page1.html", 2: "resume/page2.html"}
        template = mapping.get(page)
        if not template:
            raise HTTPException(status_code=404, detail="Not found")
        return templates.TemplateResponse(request, template, _resume_context(resolved))
    return templates.TemplateResponse(request, "resume/view.html", _resume_context(resolved))
```

## Data in `data/resume.json`

- Single source of truth for name, contact, experience, education, skills, etc.
- `contact.portfolio` holds the plain base URL for the site. It is not printed on the resume: the header carries the LinkedIn and GitHub links, which a reader can follow without a code.
- Loaded **once at import**. A missing or malformed file is logged at `exception` level and falls back to `{}` so the app stays up (pages render empty rather than crashing).
- Optional keys render only when present (`{% if %}` guarded), so a project or school entry that omits them looks exactly as it did before they existed:
  - `education[].status`, a short line under the degree (for example a graduation status).
  - `projects[].status_line`, a build-state line directly under the tech stack, above `highlights`, styled with `.demo-line`.
- Projects carry one shared `Live demos of selected projects are hosted on my portfolio. Source code for these projects is public on GitHub.` line.
- `variants` names the project order per variant. See Variants below.
- A project with a live demo carries a `url` in `resume.json`, rendering a `Live demo: <url>` line under its tech stack. Projects without one (GateKeeper, halted) omit it via the `{% if proj.url %}` guard.
- No DB and no migrations. Edit the JSON and reload.

## Route Registration

Router is `APIRouter(prefix="/resume")` and aggregated in `apps/routes/__init__.py`.

## Templates

| Template | Used when | Purpose |
|----------|-----------|---------|
| `resume/index.html` | `GET /resume/` | Hub: the variant selector, then both sheets as iframes |
| `resume/view.html` | `GET /resume/view` (no `page`) | Combined two-page document, which is what Save-as-PDF prints |
| `resume/page1.html` | `GET /resume/view?page=1` | Single page 1, used by the iframes |
| `resume/page2.html` | `GET /resume/view?page=2` | Single page 2, used by the iframes |
| `resume/_page1_body.html` | included by page1 + view | Page 1 content, one copy |
| `resume/_page2_body.html` | included by page2 + view | Page 2 content, one copy |
| `resume/_resume_css.html` | included by all three | Shared layout rules, one copy |
| `resume/_theme.html` | included by all three | The one theme: colours, typography, print rules |

The print templates (`page1.html`, `page2.html`, `view.html`) are standalone documents. They do NOT extend `apps/templates/base.html` (only the `index.html` hub does).

The markup and the styles are **partials** rather than copies. They used to be three copies of the same document and they drifted, which is how the printed PDF came to cut the last section off page 1 while the iframe beside it looked correct. A change to the resume is now a change in one file.

## Variants

The resume serves two audiences, and one running order cannot lead for both.

| Variant | Leads with | Projects |
|---|---|---|
| `mechanical` (default) | MELE Review, whose subject is mechanical | MELE Review, Water Billing System, GateKeeper, Homelab |
| `software` | Water Billing System, the largest complete build | Water Billing System, GateKeeper, Homelab, PracticeForge, MELE Review |

- The variant is a **projection**, never a second data file: it names a project
  order, and the text of each project lives once in `projects`. The two variants
  cannot disagree about what a project says, and adding a third is a data change.
- `mechanical` drops one project. Every other entry is engineering work a
  mechanical recruiter can read as process; PracticeForge is the one with neither
  an engineering subject nor a product purpose, and it is recorded as halted for
  lack of productive use.
- An unknown or missing variant falls back to `mechanical` rather than erroring,
  so a stale bookmark renders a resume instead of a 500.
- Nothing else differs between the variants. Same summary, experience, skills,
  education.

## Themes

There is one. There were three behind a selector on `/resume/`; the selector is
gone and the other two were deleted rather than left reachable by hand-editing
the query string. `?theme=N` is accepted and ignored, so an old link still
renders.

Print: use the combined `view.html` (no `page` param) and the browser's print
dialog, which produces exactly two A4 pages in either variant.

## URLs

```
/resume/                          → hub, mechanical (default)
/resume/?variant=software         → hub, software
/resume/view                      → combined, mechanical
/resume/view?variant=software     → combined, software
/resume/view?page=1               → page 1 only
/resume/view?page=2&variant=software → page 2 only, software
/resume/view?page=3               → 404 (only 1 and 2 exist)
/resume/view?theme=2              → ignored, renders the one theme
```

## Static Assets

- Portrait photo: `static/assets/images/resume_image.JPG`
- No additional JS for the resume. It is pure FastAPI + Jinja2 + CSS for reliable printing.

## Metric Note

The thesis entry cites `86.96% validation accuracy`. That figure is validation accuracy on the thesis author's reference dataset, a single authored split, not a benchmark protocol or a cross-dataset comparison. It is reported as measured, and it is not comparable with published signature-verification benchmarks.

`<FILL: dataset size / split>`

## Crawler Discouragement

- `/robots.txt` is **no longer an app route**: GateKeeper serves it from a custom page, so the file is answered before the request reaches this app. The body is unchanged (`User-agent: *` + `Disallow: /`).
- Primary noindex signal is the `X-Robots-Tag: noindex, nofollow` header set at the site-block level in `caddy/Caddyfile`, so it covers app routes, `/static` assets, and the separately-containerised documentation service. The resume print templates do not extend `base.html`, so the `<meta name="robots">` tag there is defence-in-depth for `base.html` pages only.
