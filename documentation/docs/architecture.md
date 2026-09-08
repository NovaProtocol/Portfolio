# Architecture

## Stack at a Glance

| Layer | Choice |
|-------|--------|
| Runtime | Python 3.14-slim, `granian` (prod, 1 worker) / `uvicorn --reload` (dev) |
| Framework | FastAPI modular — `create_app()` factory in `apps/__init__.py`, APIRouters in `apps/routes/` |
| Config | `apps/config.py` — `Settings(BaseSettings)` via `pydantic-settings`, `get_config()` cached |
| Templates | Jinja2 via `apps/templating.py` — `apps/templates/base.html` shared, per-route `templates/<sector>/` |
| Static | `static/` served at `/static` via `StaticFiles` mounted in `create_app()` |
| Data | `data/resume.json` (JSON, no DB) + `apps/data.py:PROJECTS` dict |
| Proxy | `caddy:2-alpine` on `:7011`, loopback-only `127.0.0.1:7011:7011`, joins `gatekeeper_dynamic` — wildcard gate `gatekeeper_caddy:7000 → gatekeeper_auth:8001` |
| Docs | MkDocs Material on `:8005` (`portfolio_documentation`), FastAPI + granian, via Caddy `/documentation/*` |
| Auth | Wildcard GateKeeper at the edge (`gatekeeper_dynamic`); the FastAPI app holds zero auth code |

---

## Modular Layout (Portfolio shape — canonical)

```
Portfolio/
├── run.py                 # argparse --mode debug/production → uvicorn factory
├── wsgi.py                # ASGI target wsgi:app (FastAPI, granian)
├── apps/
│   ├── __init__.py        # create_app() → FastAPI + RequestID/SecurityHeaders + StaticFiles + routers
│   ├── config.py          # Settings(BaseSettings) + get_config() cached
│   ├── errors.py          # install_error_handlers + structlog + {error:{code,message,request_id}}
│   ├── middleware.py      # RequestIDMiddleware + SecurityHeadersMiddleware
│   ├── tags.py            # TAG_LINKS + tech_tag() helper
│   ├── templating.py      # Jinja2Templates
│   ├── templates/base.html
│   ├── routes/            # APIRouters
│   │   ├── __init__.py    # aggregates home + projects + resume routers
│   │   ├── home.py        # GET / , GET /health
│   │   ├── projects.py    # GET /projects/ , GET /projects/info/{slug}/
│   │   └── resume.py      # GET /resume/ , GET /resume/view
│   └── data.py            # PROJECTS dict + helpers
├── static/
│   ├── assets/images/{portfolio-qr,resume_image,water-billing-system}/
│   └── js/code-demo/      # engine + registrar + demos/{caddy,docker,...}.js
├── data/resume.json
├── caddy/Caddyfile + Dockerfile
├── documentation/         # MkDocs site — FastAPI on :8005
├── Dockerfile             # python:3.14-slim → granian wsgi:app on :8000
└── compose.yaml           # app + caddy + documentation
```

The split into `apps/` sectors was chosen because Portfolio has genuinely distinct purposes (marketing home, project catalog, printable resume) that scale independently — per house convention (modular when sectors scale independently). A tiny single-purpose app would stay a monolithic `app.py` (GateKeeper shape); Portfolio graduated to sectors.

---

## App Factory

```python
# apps/__init__.py (trimmed)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apps.config import get_config
from apps.middleware import RequestIDMiddleware, SecurityHeadersMiddleware

def create_app() -> FastAPI:
    config = get_config()
    app = FastAPI(title="Portfolio", debug=config.DEBUG)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.include_router(router)
    install_error_handlers(app, templates)
    return app
```

- Factory reads `get_config()` (BaseSettings, env via compose `${VAR:?}`), mounts `StaticFiles`, installs `RequestIDMiddleware` + `SecurityHeadersMiddleware` + `errors` handlers.
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
# wsgi.py — ASGI target
from apps import create_app
app = create_app()
```

```python
# run.py — argparse --mode
import argparse, os
parser.add_argument("--mode", choices=["debug","production"])
os.environ["DEPLOYMENT_TYPE"] = args.mode
uvicorn.run("apps:create_app", factory=True, host="0.0.0.0", port=8000, reload=args.mode=="debug")
```

- Env is read via `BaseSettings` from compose `${DEPLOYMENT_TYPE:?}` — no `.env` file.
- `wsgi.py` is `create_app()` ASGI target for `granian --interface asgi wsgi:app`.
- Production uses `Dockerfile CMD ["granian", "--interface", "asgi", "...", "wsgi:app"]`; dev uses `uvicorn` with reload.

## Request Flow

```mermaid
sequenceDiagram
    participant Browser
    participant Caddy as Caddy :7011
    participant GK as GateKeeper wildcard caddy:7000→auth:8001
    participant App as portfolio_main:8000

    Browser->>Caddy: GET /projects/info/gatekeeper
    Caddy->>GK: GET /api/authz/forward-auth via gatekeeper_dynamic<br/>X-Forwarded-Uri: /projects/info/gatekeeper
    alt valid gatekeeper_token cookie or ?access_code=
        GK-->>Caddy: 200
        Caddy->>App: reverse_proxy portfolio_main:8000
        App-->>Caddy: TemplateResponse projects/detail.html
        Caddy-->>Browser: 200 HTML
    else no credential
        GK-->>Caddy: 302 → https://gatekeeper.apex/?redirect=...
        Caddy-->>Browser: 302 Location (relay)
    end

    Note over Caddy,App: Gate is at wildcard gatekeeper_dynamic;<br/>local Caddy has no per-app forward_auth<br/>handle /health { reverse_proxy portfolio_main:8000 }
```

- App itself sees no auth — the wildcard gate enforces it. The app only renders pages and serves `/static` via `StaticFiles`.
- Health: `GET /health` returns `{"status":"ok"}` JSON and is the compose `healthcheck` target (`python -c urllib.request.urlopen(http://127.0.0.1:8000/health)`).

## Data Layer

No database — the only persistent content is:

- `apps/data.py:PROJECTS` — dict of project metadata (titles, descriptions, tech stacks, links). `ordered_projects()` in `apps/routes/projects.py` returns active entries.
- `data/resume.json` — loaded once at import in `apps/routes/resume.py:_load_resume()`. Missing or malformed JSON logs and returns `{}`.

This keeps the portfolio a **single deployable** with no volumes or migrations.

## Security & Auth

- Gate is at the wildcard (`gatekeeper_caddy:7000` → `gatekeeper_auth:8001` on `gatekeeper_dynamic`) — local `caddy/Caddyfile` has no per-app `forward_auth` (per `reference/gatekeeper/caddy-setup.md` wildcard primary). Apex `gatekeeper_token` cookie (HttpOnly, Lax) covers all subdomains.
- No per-app accounts in Portfolio itself (reserved `SECRET_KEY` in config for future use).
- `RequestIDMiddleware` + `SecurityHeadersMiddleware` on every response; `X-Request-ID` propagated to `structlog` context and error envelope `{error:{code,message,request_id}}`.

## Errors

JS: `console.error({status, request_id, stack})` + toast; Server: `structlog` JSON + `X-Request-ID` to docker logs; envelope `{error:{code,message,request_id}}`. No traceback to client.

## Formatting Conventions

- `from __future__ import annotations` on every module.
- `ruff` with `line-length = 100`, `quote-style = "double"`, `isort` with `known-first-party = ["apps"]`.
- `requirements.txt` uses `>=` lower bounds (`fastapi>=0.115`, `granian>=2`) — no `==` pins unless justified.
