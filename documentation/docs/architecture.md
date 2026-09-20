# Architecture

## Stack at a Glance

| Layer | Choice |
|-------|--------|
| Runtime | Python 3.14-slim, `granian` (prod, 1 worker) / `uvicorn --reload` (dev) |
| Framework | FastAPI modular with `create_app()` factory in `apps/__init__.py` and APIRouters in `apps/routes/` |
| Config | `apps/config.py` using `Settings(BaseSettings)` via `pydantic-settings` with `get_config()` cached |
| Templates | Jinja2 via `apps/templating.py` with `apps/templates/base.html` shared and per-route `templates/<sector>/` |
| Static | `static/` served at `/static` via `StaticFiles` mounted in `create_app()`; cache lifespans applied by `CacheControlMiddleware` |
| Data | `data/resume.json` (JSON, no DB) + `apps/data.py:PROJECTS` dict |
| Proxy | `caddy:2-alpine` on `:7011` with loopback-only `127.0.0.1:7011:7011` joining `gatekeeper`. Gate is `gatekeeper_caddy:7000 → gatekeeper_auth:8001` |
| Docs | MkDocs Material on `:8005` (`portfolio_documentation`), FastAPI + granian, via Caddy `/documentation/*` |
| Auth | GateKeeper at the edge (`gatekeeper`); the FastAPI app holds zero auth code |

---

## Modular Layout (Portfolio shape, canonical)

```
Portfolio/
├── run.py # argparse --mode debug/production → uvicorn factory
├── wsgi.py # ASGI target wsgi:app (FastAPI, granian)
├── apps/
│ ├── __init__.py # create_app() → FastAPI + RequestID/SecurityHeaders + StaticFiles + routers
│ ├── config.py # Settings(BaseSettings) + get_config() cached
│ ├── errors.py # install_error_handlers + structlog + {error:{code,message,request_id}}
│ ├── middleware.py # RequestID + SecurityHeaders + CacheControl
│ ├── tags.py # TAG_LINKS + tech_tag() helper
│ ├── templating.py # Jinja2Templates
│ ├── templates/base.html
│ ├── routes/ # APIRouters
│ │ ├── __init__.py # aggregates home + projects + resume routers
│ │ ├── home.py # GET / , GET /health
│ │ ├── projects.py # GET /projects/ , GET /projects/info/{slug}/
│ │ └── resume.py # GET /resume/ , GET /resume/view
│ └── data.py # PROJECTS dict + helpers
├── static/
│ ├── assets/images/{resume_image,water-billing-system}/
│ └── js/code-demo/ # engine + registrar + demos/{caddy,docker,...}.js
├── data/resume.json
├── caddy/Caddyfile + Dockerfile
├── documentation/ # MkDocs site with FastAPI on :8005
├── Dockerfile # python:3.14-slim → granian wsgi:app on :8000
└── compose.yaml # app + caddy + documentation
```

The split into `apps/` sectors was chosen because Portfolio has genuinely distinct purposes (marketing home, project catalog, printable resume) that scale independently under the house convention for modular sectors that scale independently. A tiny single-purpose app would stay a monolithic `app.py` (GateKeeper shape), while Portfolio graduated to sectors.

---

## App Factory

```python
# apps/__init__.py (trimmed)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apps.config import get_config
from apps.middleware import CacheControlMiddleware, RequestIDMiddleware, SecurityHeadersMiddleware

def create_app() -> FastAPI:
 config = get_config()
 app = FastAPI(title="Portfolio", debug=config.DEBUG)
 app.add_middleware(RequestIDMiddleware)
 app.add_middleware(SecurityHeadersMiddleware)
 app.add_middleware(CacheControlMiddleware, is_debug=config.DEBUG)
 app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
 app.include_router(router)
 install_error_handlers(app, templates)
 return app
```

- Factory reads `get_config()` (BaseSettings with env via compose `${VAR:?}`), mounts `StaticFiles`, and installs `RequestIDMiddleware`, `SecurityHeadersMiddleware`, `CacheControlMiddleware`, and the `errors` handlers.
- No env reads outside `get_config()`, no DB, no global state.
- `from __future__ import annotations` on every module (house style).

## Config & Entrypoints

```python
# apps/config.py
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
 DEPLOYMENT_TYPE: str = Field(default="debug")
 SECRET_KEY: str | None = Field(default=None)
 @property
 def DEBUG(self) -> bool: return self.DEPLOYMENT_TYPE.lower() == "debug"
```

```python
# wsgi.py provides the ASGI target
from apps import create_app
app = create_app()
```

```python
# run.py provides argparse --mode
import argparse, os
parser.add_argument("--mode", choices=["debug","production"])
os.environ["DEPLOYMENT_TYPE"] = args.mode
uvicorn.run("apps:create_app", factory=True, host="0.0.0.0", port=8000, reload=args.mode=="debug")
```

- Env is read via `BaseSettings` from compose `${DEPLOYMENT_TYPE:?}` with no `.env` file.
- `wsgi.py` is the `create_app()` ASGI target for `granian --interface asgi wsgi:app`.
- Production uses `Dockerfile CMD ["granian", "--interface", "asgi", "...", "wsgi:app"]` while dev uses `uvicorn` with reload.

## Request Flow

```mermaid
sequenceDiagram
 participant Browser
 participant Caddy as Caddy :7011
 participant GK as GateKeeper wildcard caddy:7000→auth:8001
 participant App as portfolio_main:8000

 Browser->>Caddy: GET /projects/info/gatekeeper
 Caddy->>GK: GET /api/authz/forward-auth via gatekeeper<br/>X-Forwarded-Uri: /projects/info/gatekeeper
 alt valid gatekeeper_token cookie or ?access_code=
 GK-->>Caddy: 200
 Caddy->>App: reverse_proxy portfolio_main:8000
 App-->>Caddy: TemplateResponse projects/detail.html
 Caddy-->>Browser: 200 HTML
 else no credential
 GK-->>Caddy: 302 → https://gatekeeper.apex/?redirect=...
 Caddy-->>Browser: 302 Location (relay)
 end

 Note over Caddy,App: Gate is at gatekeeper;<br/>local Caddy has no per-app GateKeeper gate<br/>handle /health { reverse_proxy portfolio_main:8000 }
```

- App itself sees no auth because the gate enforces it. The app only renders pages and serves `/static` via `StaticFiles`.
- Health: `GET /health` returns `{"status":"ok"}` JSON and is the compose `healthcheck` target (`python -c urllib.request.urlopen(http://127.0.0.1:8000/health)`).
- Crawler discouragement: the primary noindex signal is the `X-Robots-Tag: noindex, nofollow` header at the site-block level in `caddy/Caddyfile` (covers app, `/static`, and the separately-containerised docs service), with a `<meta name="robots">` tag in `base.html` as defence-in-depth. `/robots.txt` is **no longer served by the app**: GateKeeper answers it from a custom page, matched by `*.projectnova.download/robots.txt` and served only where the host's rules allow `none` (Portfolio's group and the apex do). See the GateKeeper docs § Custom Pages.

## Cache Headers

Cache behavior is decided in the app, not in Cloudflare or the `Caddyfile`. `CacheControlMiddleware` takes one boolean (`config.DEBUG`) and sets `Cache-Control` on every response after the handler runs, so mounted `StaticFiles`, HTML routes, `/health`, and error pages are all covered by a single mechanism (a `StaticFiles` wrapper would cover only `/static`).

- **`DEPLOYMENT_TYPE=DEBUG`** (`config.DEBUG`, case-insensitive), overwrites `Cache-Control` on every response with exactly `no-store`. `no-cache` is weaker: it still permits a cache to store gated bytes and only forces revalidation, and `private` still permits storing on shared infrastructure. `no-store` forbids storing outright. Overwriting rather than filling gaps means no route can accidentally stay public.
- **Any other value (production)**: fills `Cache-Control` only when the handler set none, so an explicit route header stays authoritative. Lifespans are `UPPER_SNAKE_CASE` constants at the top of `apps/middleware.py`; retuning one is a one-line edit plus a redeploy (deliberately not env vars, four integers do not justify new required config).

| Class | Paths | Header |
|-------|-------|--------|
| Static assets | `/static/*` | `public, max-age=86400` |
| Misc small | `/health` | `public, max-age=3600` |
| HTML (default) | everything else | `private, max-age=300` |

Why this matters: an origin that sends no `Cache-Control` but does send `ETag` / `Last-Modified` is heuristically cacheable, which is how gated images ended up stored at the edge. Sending an explicit header removes that ambiguity, either a deliberate lifespan or `no-store`.

`no-store` stops *future* stores; it does not evict a copy already sitting at the edge. Existing entries expire on their own schedule and revalidation then returns the new headers.

### Reusable pattern

Portable to the sibling apps (GateKeeper auth-gateway, WBS portals/api, MELEReviewSite, SolveSpace `solver_private`, NovaProtocol): one `BaseHTTPMiddleware` constructed with `is_debug`, DEBUG overwriting `no-store` everywhere, production filling gaps per path class, route-level explicit headers left authoritative. Before applying it to MELEReviewSite, resolve why `melereview_web` runs with an empty `DEPLOYMENT_TYPE`, an empty value falls back to the `debug` default locally but is untested through its compose path.

## Data Layer

No database. The only persistent content is:

- `apps/data.py:PROJECTS` holds the dict of project metadata (titles, descriptions, tech stacks, links). `ordered_projects()` in `apps/routes/projects.py` returns active entries.
- `data/resume.json` loads once at import in `apps/routes/resume.py:_load_resume()`. Missing or malformed JSON logs and returns `{}`.

This keeps the portfolio a **single deployable** with no volumes or migrations.

## Security & Auth

- Gate is at the wildcard (`gatekeeper_caddy:7000` → `gatekeeper_auth:8001` on `gatekeeper`). Local `caddy/Caddyfile` has zero per-app `forward_auth`; the wildcard is the primary gate. Apex `gatekeeper_token` cookie (HttpOnly, Lax) covers all subdomains.
- No per-app accounts in Portfolio itself (reserved `SECRET_KEY` in config for future use).
- `RequestIDMiddleware` + `SecurityHeadersMiddleware` on every response, with `X-Request-ID` propagated to `structlog` context and error envelope `{error:{code,message,request_id}}`.

## Errors

JS: `console.error({status, request_id, stack})` + toast. Server: `structlog` JSON + `X-Request-ID` to docker logs with envelope `{error:{code,message,request_id}}`. No traceback to client.

## Formatting Conventions

- `from __future__ import annotations` on every module.
- `ruff` with `line-length = 100`, `quote-style = "double"`, `isort` with `known-first-party = ["apps"]`.
- `requirements.txt` uses `>=` lower bounds (`fastapi>=0.115`, `granian>=2`) with no `==` pins unless justified.
