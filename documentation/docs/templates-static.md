# Templates & Static

## Layout

- **Shared base:** `apps/templates/base.html` where blueprinted pages extend it, so nav, footer, and layout are defined once. The standalone resume print templates (`resume/page1.html`, `page2.html`, `view.html`) are the exception, and they do not extend `base.html`.
- **Per-route templates:** `apps/templates/<sector>/*.html` namespaced by sector (`home/index.html`, `projects/index.html`, `projects/detail.html`, `resume/view.html`, etc.). Jinja2 `templates` from `apps/templating.py` resolves the shared `apps/templates/` folder.
- **Static:** `static/` served at `/static` via `StaticFiles` mounted in `create_app()` (`app.mount("/static", StaticFiles(...))`). Referenced in templates with `url_for('static', path='…')`. Cache lifespans come from `CacheControlMiddleware`: `public, max-age=86400` for `/static/*` in production, `no-store` everywhere while `DEPLOYMENT_TYPE=DEBUG` and the response sets no header of its own. See `architecture.md` → Cache Headers and [Caching](caching.md).

```
apps/
├── templates/base.html
├── home/templates/home/index.html
├── projects/templates/projects/{index,detail,_card}.html
└── resume/templates/resume/{index,view,page1,page2,_theme}.html
    resume/templates/resume/{_page1_body,_page2_body,_resume_css}.html  (partials)
static/
├── assets/images/
│ ├── resume_image.JPG
│ └── water-billing-system/water-billing-system-preview.png
└── js/code-demo/
 ├── engine.js, registrar.js, demos.js
 └── demos/{caddy,docker,flask,git,gunicorn,cloudflare,react-native}.js
```

## Base Template

`apps/templates/base.html` provides the common shell (doctype, head, nav, main block, footer). Child templates override `title` / `content` blocks and call helpers from `apps/tags.py`.

## Tags Helpers in `apps/tags.py`

```python
from markup safe import Markup, escape

TAG_LINKS: dict[str, str] = {
 "Flask": "https://flask.palletsprojects.com/",
 "Gunicorn": "https://gunicorn.org/",
 "Docker": "https://www.docker.com/",
 # ~40 entries covering Python, JS, infra, design, and hardware
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

## Static Demos in `static/js/code-demo/`

Small interactive code demos embedded on project detail pages:

- `engine.js` runs the demo lifecycle.
- `registrar.js` registers demos by name.
- `demos.js` is the index that imports `demos/*.js` (`caddy`, `docker`, `flask`, `gunicorn`, `cloudflare`, `git`, `react-native`).

Each demo is a self-contained JS module that renders a live config / command example for that project's stack.

## Adding Assets

- Images for new projects: `static/assets/images/<slug>/preview.png` → referenced as `image: "assets/images/<slug>/preview.png"` in `PROJECTS` (the template prefixes `/static/` via `url_for`).
- Reuse `TAG_LINKS` for tech tags. Add a new entry when a novel stack appears so the tag becomes clickable.
- For resume or marketing visuals, keep assets under `static/assets/images/` so the `StaticFiles` mount serves them without extra Caddy config.
- Filenames carry no content hash, so replacing an asset in place keeps the same URL. Static assets are cached for 24h in production (see `architecture.md` → Cache Headers); with `DEPLOYMENT_TYPE=DEBUG` every response that sets no header of its own is `no-store` and replacements are visible immediately.

## Errors

JS: `console.error({status, request_id, stack})` + toast. Server: `structlog` JSON + `X-Request-ID` to docker logs with envelope `{error:{code,message,request_id}}`. No traceback to client.

## No Build Step

No Vite/Webpack/Tailwind build. CSS and JS are plain static files served directly. This keeps the image small and the Dockerfile a single `COPY . .`.

## The contact control

The header's **Contact** is an `<a href="mailto:...">` that opens a panel when `static/js/contact.js` is running, rather than a `<button>`. A button with no script behind it is dead, which is worse than the problem it solves, so the mailto stays underneath as the no-JavaScript fallback.

The panel exists because a `mailto:` is a correct link that does nothing at all on a machine with no mail handler - the click lands, no window opens, and the control reads as broken. It therefore offers the address in text, a copy control, the mailto for a reader who does have a mail app, and a web-compose link that needs neither. The home page's contact section carries the same address and the same copy control for the same reason.

- The address is **one value**: `CONTACT_EMAIL` in `apps/config.py`, exposed to templates as the `contact_email` global in `apps/templating.py`. Nothing types it into a template, so the header and the section cannot drift apart, and the environment can override it.
- A copy control is `<button data-contact-copy data-copy-value="<address>">`, with a `[data-contact-status]` element as its `role="status"` live region somewhere above it in the tree, because a copy that announces nothing announces nothing. `contact.js` walks up to find the nearest.
- The panel's styles are plain CSS in `base.html`'s `head_assets` block, not Tailwind utilities: the compiled stylesheet is a build artifact and a class that is not in it is a silent no-op.
- Changing the script means bumping its `?v=` in `base.html`; static assets are cached for 24h in production and the filename carries no content hash.
