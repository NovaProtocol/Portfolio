# Resume Blueprint

**Module:** `apps/routes/resume.py` using `APIRouter(prefix="/resume")`

Renders the resume from two data files. One visual theme, two printable pages,
a combined view, and a **list of named resumes**: the generic one, plus a named
entry for each application that needs different emphasis.

The resume itself lives in `data/default_resume.json`. `data/overwrite_resume.json`
holds the named resumes, each carrying only the parts it changes.

## Routes

| Route | Handler | Query params | Description |
|-------|---------|--------------|-------------|
| `GET /resume/` | `apps.routes.resume.index` | `resume=<name>` (default `Generic`) | Resume hub rendering `resume/index.html`, with the resume selector |
| `GET /resume/view` | `apps.routes.resume.view` | `resume=<name>`, `page=1,2` (optional) | Single or combined page using `resume/view.html` (both pages) or `resume/page1.html` / `page2.html` for print |

`?variant=` and `?theme=` were both real parameters once. They are accepted and
ignored rather than rejected, so a link made before either rename still renders.

```python
# apps/routes/resume.py (trimmed)
_DATA = Path(__file__).resolve().parent.parent.parent / "data"
_DEFAULT_PATH = _DATA / "default_resume.json"
_OVERWRITE_PATH = _DATA / "overwrite_resume.json"

DEFAULT_RESUME = "Generic"

def _deep_merge(base: dict, override: dict) -> dict:
    """`override` over `base`, recursively. Lists are replaced, not merged."""
    out = copy.deepcopy(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out

def _expand_projects(resume: dict) -> dict:
    """Replace each project named in a list with the project itself."""
    projects = resume.get("projects")
    if not isinstance(projects, list) or not all(isinstance(p, str) for p in projects):
        return resume
    by_name = {p.get("name"): p for p in resume.get("project_pool") or []}
    return {**resume, "projects": [by_name[n] for n in projects if n in by_name]}

@router.get("/view", response_class=HTMLResponse)
async def view(request: Request, page: int | None = None, resume: str = DEFAULT_RESUME):
    resolved = _normalise_resume(resume)
    ...
```


## Data

Two files, and the split is the point.

**`data/default_resume.json`** is the resume. It is served as **Generic**, the
general-purpose one for a job fair where you do not know who is reading, and it
is the base every named resume is built from.

**`data/overwrite_resume.json`** is a list of named resumes. Each names itself
and carries only what it changes:

```json
[
  {
    "resume_name": "Mechanical Engineering",
    "overwrites": {
      "headline": "Mechanical Engineer | Design, safety, and documentation",
      "summary": "Mechanical Engineering graduate with hands-on experience ...",
      "projects": ["MELE Review", "Water Billing System", "Homelab", "GateKeeper"]
    }
  }
]
```

- The merge is **deep**. An override that sets `education` as an object changes
  only the keys it names and inherits the rest of that entry.
- **Lists are replaced, not concatenated.** A shorter `projects` list is a
  deliberate choice about what to show; merging would produce a resume nobody
  wrote.
- `projects` in an override names projects rather than restating them. The
  content of every project lives in the default, once, so the two files cannot
  drift and a project is edited in one place no matter how many resumes show it.
- The served list is **Generic plus every override**, in file order. An unknown
  or missing name falls back to Generic rather than erroring, so a stale bookmark
  still renders a resume.
- Loaded once at import. A missing or malformed file is logged at `exception`
  level and falls back, so the rest of the site stays up.
- `contact.portfolio` holds the plain base URL for the site. It is not printed on
  the resume: the header carries the LinkedIn and GitHub links, which a reader can
  follow without a code.
- Optional keys render only when present (`{% if %}` guarded), so a project or
  school entry that omits them looks exactly as it did before they existed:
  - `education[].status`, a short line under the degree (for example a graduation status).
  - `projects[].status_line`, a build-state line directly under the tech stack, above `highlights`, styled with `.demo-line`.
- Projects carry one shared `Live demos of selected projects are hosted on my portfolio. Source code for these projects is public on GitHub.` line.
- A project with a live demo carries a `url`, rendering a `Live demo: <url>` line under its tech stack. Projects without one omit it via the `{% if proj.url %}` guard.
- No DB and no migrations. Edit the JSON and restart.

### Adding a resume

Add one entry to `data/overwrite_resume.json` with a `resume_name` and an
`overwrites` object holding just what differs. It appears in the selector with no
code change. `tools/resume_fit.py --resume all` measures every one.

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

## Resumes

| Resume | Headline leads with | Projects |
|---|---|---|
| Generic (default) | the degree, then what the software work is | all six, thesis build first |
| Mechanical Engineering | the degree and the mechanical work | all but PracticeForge, thesis build first |
| Software | the software work, degree mentioned second | all but the mower, largest software build first |

- A named resume is a **projection** of the default, never a second data file.
- The mechanical resume drops PracticeForge. Every other entry is engineering
  work a mechanical reader can follow; PracticeForge is a Python practice sandbox
  with neither an engineering subject nor a product purpose.
- The software resume drops the mower, the way the mechanical resume drops
  PracticeForge, and keeps every other entry. The solver and the reviewer stay,
  because they are still things this person built and shipped. Both exclusions are
  asserted as set differences against the default, so a project added later has to
  be placed on each resume deliberately rather than appearing by arithmetic.
- The mower leads Generic and Mechanical. It is the undergraduate thesis and the
  only entry that is a machine rather than a service — two LiFePO4 packs, a 400 W
  array, and a panel that commands the drives.
- **The headline is the part that matters most between them.** A reader who sees
  "Mechanical Engineering graduate" first has filed the application before
  reaching the deployed projects, so the software resume does not lead with the
  degree. It still cannot imply a Computer Science degree: the education entry is
  inherited unchanged, and a test asserts no resume claims one.
- Nothing else differs. Same experience, education, skills.

## URLs

```
/resume/                                    → hub, Generic (default)
/resume/?resume=Mechanical%20Engineering    → hub, mechanical
/resume/view                                → combined, Generic
/resume/view?resume=Mechanical%20Engineering → combined, mechanical
/resume/view?page=1                         → page 1 only
/resume/view?page=2&resume=Mechanical%20Engineering → page 2 only
/resume/view?page=3                         → 404 (only 1 and 2 exist)
/resume/view?variant=mechanical             → ignored, serves Generic
/resume/view?theme=2                        → ignored, renders the one theme
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
