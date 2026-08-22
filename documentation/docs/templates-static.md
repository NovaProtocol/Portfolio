# Templates & Static

## Layout

- **Shared base:** `apps/templates/base.html` — every blueprinted page extends it, so nav, footer, and layout are defined once.
- **Per-blueprint templates:** `apps/<sector>/templates/<sector>/*.html` — namespaced by sector (`home/index.html`, `projects/index.html`, `projects/detail.html`, `resume/view.html`, etc.). Flask's template search includes both the shared folder and the blueprint's `template_folder`.
- **Static:** `static/` served at `/static` via `Flask(static_folder=str(static_dir), static_url_path="/static")` in the factory. Referenced in templates with `url_for('static', filename='…')`.

```
apps/
├── templates/base.html
├── home/templates/home/index.html
├── projects/templates/projects/{index,detail,_card}.html
└── resume/templates/resume/{index,view,page1,page2,_theme}.html
static/
├── assets/images/
│   ├── resume_image.JPG
│   ├── portfolio-qr.png
│   └── water-billing-system/water-billing-system-preview.png
└── js/code-demo/
    ├── engine.js, registrar.js, demos.js
    └── demos/{caddy,docker,flask,git,gunicorn,cloudflare,react-native}.js
```

## Base Template

`apps/templates/base.html` provides the common shell (doctype, head, nav, main block, footer). Child templates override `title` / `content` blocks and call helpers from `apps/tags.py`.

## Tags Helpers — `apps/tags.py`

```python
from markup safe import Markup, escape

TAG_LINKS: dict[str, str] = {
    "Flask": "https://flask.palletsprojects.com/",
    "Gunicorn": "https://gunicorn.org/",
    "Docker": "https://www.docker.com/",
    # ~40 entries — covers Python, JS, infra, design, hardware
}

def tech_tag(name: str) -> Markup:
    url = TAG_LINKS.get(name)
    if url:
        return Markup(
            '<a class="tag" href="{}" target="_blank" rel="noopener noreferrer">{}</a>'.format(
                escape(url), escape(name)
            )
        )
    # fallback renders a plain span
```

- Registered on the app via `tags.init_app(app)` in the factory (exposes `tech_tag` to Jinja2 globals).
- Unknown tags render without a link so the portfolio never breaks when a new stack is listed.

## Static Demos — `static/js/code-demo/`

Small interactive code demos embedded on project detail pages:

- `engine.js` — runs the demo lifecycle.
- `registrar.js` — registers demos by name.
- `demos.js` — index that imports `demos/*.js` (`caddy`, `docker`, `flask`, `gunicorn`, `cloudflare`, `git`, `react-native`).

Each demo is a self-contained JS module that renders a live config / command example for that project's stack.

## Adding Assets

- Images for new projects: `static/assets/images/<slug>/preview.png` → referenced as `image: "assets/images/<slug>/preview.png"` in `PROJECTS` (the template prefixes `/static/` via `url_for`).
- Reuse `TAG_LINKS` for tech tags — add a new entry when a novel stack appears so the tag becomes clickable.
- For resume or marketing visuals, keep assets under `static/assets/images/` so the Flask `static` mount serves them without extra Caddy config.

## No Build Step

No Vite/Webpack/Tailwind build — CSS and JS are plain static files served directly. This keeps the image small and the Dockerfile a single `COPY . .`.
