# Architecture

## Stack at a Glance

| Layer | Choice |
|-------|--------|
| Runtime | Python 3.14-slim, `gunicorn` gthread (prod), Flask dev server (dev) |
| Framework | Flask 3.1 modular — `create_app()` factory in `apps/__init__.py`, three blueprints |
| Config | `apps/config.py` — `BaseConfig` / `DebugConfig` / `ProductionConfig` + `config_dict`, selected by `DEPLOYMENT_TYPE` |
| Templates | Jinja2 via Flask — `apps/templates/base.html` shared, per-blueprint `templates/<sector>/` |
| Static | `static/` served at `/static` via `Flask(static_folder=...)` |
| Data | `data/resume.json` (JSON, no DB) + `apps/projects/routes.py:PROJECTS` dict |
| Proxy | `caddy:2-alpine` on `:7011`, loopback-only `127.0.0.1:7011:7011`, joins `gatekeeper_dynamic` — wildcard gate `gatekeeper_caddy:7000 → gatekeeper_auth:8001` |
| Docs | MkDocs Material on `:8005` (`portfolio_documentation`), FastAPI + granian, via Caddy `/documentation/*` |
| Auth | Wildcard GateKeeper at the edge (`gatekeeper_dynamic`); the Flask app holds zero auth code |

---

## Modular Layout (Portfolio shape — canonical)

```
Portfolio/
├── run.py                 # dev only — reads DEPLOYMENT_TYPE inside main, runs Flask dev server
├── wsgi.py                # gunicorn target wsgi:app (Production config, minimal, no env mutation)
├── apps/
│   ├── __init__.py        # create_app(config) + register_blueprints() + ProxyFix
│   ├── config.py          # Base/Debug/Production + config_dict
│   ├── tags.py            # TAG_LINKS + tech_tag() helper (Markup, registered via init_app)
│   ├── templates/base.html
│   ├── home/
│   │   ├── __init__.py    # home_blueprint, url_prefix=""
│   │   ├── routes.py      # GET / , GET /health
│   │   └── templates/home/index.html
│   ├── projects/
│   │   ├── __init__.py    # projects_blueprint, url_prefix="/projects"
│   │   ├── routes.py      # PROJECTS dict + ordered_projects() + / and /info/<slug>/
│   │   └── templates/projects/{index,detail,_card}.html
│   └── resume/
│       ├── __init__.py    # resume_blueprint, url_prefix="/resume"
│       ├── routes.py      # reads data/resume.json + / and /view (theme/page)
│       └── templates/resume/{index,view,page1,page2,_theme}.html
├── static/
│   ├── assets/images/{portfolio-qr,resume_image,water-billing-system}/
│   └── js/code-demo/      # engine + registrar + demos/{caddy,docker,flask,...}.js
├── data/resume.json
├── caddy/Caddyfile + Dockerfile
├── documentation/         # MkDocs site — FastAPI on :8005
├── Dockerfile             # python:3.14-slim → gunicorn wsgi:app on :8000
└── compose.yaml           # app + caddy + documentation
```

The split into `apps/` sectors was chosen because Portfolio has genuinely distinct purposes (marketing home, project catalog, printable resume) that scale independently — per house convention (modular when sectors scale independently). A tiny single-purpose app would stay a monolithic `app.py` (GateKeeper shape); Portfolio graduated to sectors.

---

## App Factory

```python
# apps/__init__.py
from __future__ import annotations

from importlib import import_module
from pathlib import Path

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from apps import tags


def register_blueprints(app: Flask) -> None:
    for module_name in ("home", "projects", "resume"):
        module = import_module("apps.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)


def create_app(config: object) -> Flask:
    static_dir = Path(__file__).resolve().parent.parent / "static"
    app = Flask(__name__, static_folder=str(static_dir), static_url_path="/static")
    app.config.from_object(config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    tags.init_app(app)
    register_blueprints(app)
    return app
```

- No env reads, no DB hits, no global state — the factory only wires `ProxyFix` and blueprints. Config selection happens in the entrypoints.
- `ProxyFix(x_for=1, x_proto=1)` is required behind Caddy / the tunnel.
- `from __future__ import annotations` on every module (house style).

## Config & Entrypoints

```python
# apps/config.py
from __future__ import annotations


class BaseConfig:
    pass


class DebugConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


config_dict = {"Debug": DebugConfig, "Production": ProductionConfig}
```

```python
# run.py — dev only, env inside main
from __future__ import annotations
import os, sys
from apps import create_app
from apps.config import config_dict

if __name__ == "__main__":
    mode = os.environ.get("DEPLOYMENT_TYPE", "").upper()
    if mode not in ("DEBUG", "PRODUCTION"):
        print("FATAL: DEPLOYMENT_TYPE must be DEBUG or PRODUCTION", file=sys.stderr)
        sys.exit(1)
    app = create_app(config_dict["Debug" if mode == "DEBUG" else "Production"])
    if mode == "DEBUG":
        app.run(host="0.0.0.0", port=8000, debug=True)
```

```python
# wsgi.py — minimal, no env mutation, gunicorn target
from __future__ import annotations
from apps import create_app
from apps.config import config_dict

app = create_app(config_dict["Production"])
```

- Env is read from `os.environ` only — no `load_dotenv`, no `.env` file. Compose interpolates `${DEPLOYMENT_TYPE:?…}`.
- `wsgi.py` does not set `os.environ["DEPLOYMENT_TYPE"]` or import `run` — the container already has the env var; the Dockerfile CMD is `gunicorn … wsgi:app`.
- `run.py` deliberately has **no** `StandaloneApplication(BaseApplication)` gunicorn embedding — the deprecated pattern is removed; production uses the Dockerfile CMD.

## Request Flow

```mermaid
sequenceDiagram
    participant Browser
    participant Caddy as Caddy :7011
    participant GK as GateKeeper wildcard caddy:7000→auth:8001
    participant Flask as portfolio_main:8000

    Browser->>Caddy: GET /projects/info/gatekeeper
    Caddy->>GK: GET /api/authz/forward-auth via gatekeeper_dynamic<br/>X-Forwarded-Uri: /projects/info/gatekeeper
    alt valid gatekeeper_token cookie or ?access_code=
        GK-->>Caddy: 200
        Caddy->>Flask: reverse_proxy portfolio_main:8000
        Flask-->>Caddy: render projects/detail.html
        Caddy-->>Browser: 200 HTML
    else no credential
        GK-->>Caddy: 302 → https://gatekeeper.apex/?redirect=...
        Caddy-->>Browser: 302 Location (relay)
    end

    Note over Caddy,Flask: Gate is at wildcard gatekeeper_dynamic;<br/>local Caddy has no per-app forward_auth<br/>handle /health { reverse_proxy portfolio_main:8000 }
```

- Flask itself sees no auth — the wildcard gate enforces it. The app only renders pages and serves `/static`.
- Health: `GET /health` returns `{"status":"ok"}` JSON and is the compose `healthcheck` target (`python -c urllib.request.urlopen(http://127.0.0.1:8000/health)`).

## Data Layer

No database — the only persistent content is:

- `apps/projects/routes.py:PROJECTS` — dict of project metadata (titles, descriptions, tech stacks, links). `ordered_projects()` returns active entries.
- `data/resume.json` — loaded once at import in `apps/resume/routes.py:_load_resume()`. Missing or malformed JSON logs and returns `{}`.

This keeps the portfolio a **single deployable** with no volumes or migrations.

## Security & Auth

- Gate is at the wildcard (`gatekeeper_caddy:7000` → `gatekeeper_auth:8001` on `gatekeeper_dynamic`) — local `caddy/Caddyfile` has no per-app `forward_auth` (per `reference/gatekeeper/caddy-setup.md` wildcard primary). Apex `gatekeeper_token` cookie (HttpOnly, Lax) covers all subdomains.
- No per-app accounts, no `itsdangerous` cookie signing in Portfolio itself (reserved `SECRET_KEY` in `.env.example` for future use).
- Flask `ProxyFix` ensures `request.scheme` and `remote_addr` are correct behind the tunnel.

## Formatting Conventions

- `from __future__ import annotations` on every module.
- `ruff` with `line-length = 100`, `quote-style = "double"`, `isort` with `known-first-party = ["apps"]`.
- `requirements.txt` uses `>=` lower bounds (`flask>=3.1`, `gunicorn>=26.0`) — no `==` pins unless justified.
