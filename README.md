# Portfolio

Personal portfolio site built with Python 3.14 + FastAPI + Granian + Jinja2, served behind a Caddy reverse proxy that gates access through [GateKeeper](https://github.com/NovaProtocol/GateKeeper).

**Stack:** Python 3.14 + FastAPI + Granian + Jinja2 + Caddy 2-alpine. The FastAPI app runs under granian (ASGI, 1 worker) with Jinja2 templates and StaticFiles.

## How it works

```text
Browser → GateKeeper (wildcard, apex domain)
            └─ 200 on pass → Caddy :7011
                                   ├─ /health          → portfolio_main:8000
                                   ├─ /documentation/* → portfolio_documentation:8005
                                   └─ everything else  → portfolio_main:8000
```

`portfolio_main` is the FastAPI app: one template tree split across `apps/home`, `apps/projects` and `apps/resume`, a `PROJECTS` dict that drives the project list and detail pages, and a middleware stack that adds a request id, security headers and cache-control. `portfolio_documentation` is the MkDocs site in `documentation/`. Caddy is the only published port and holds no per-app auth — the gate is at the apex wildcard, so every path is decided by GateKeeper rules before Caddy sees the request.

## Adding a Project

Add an entry to the `PROJECTS` dict in `apps/projects/routes.py`:

```python
"my-project": {
    "title": "My Project",
    "subtitle": "Client or context",
    "description": "What it does, who it's for, what it solves.",
    "tech": {
        "web": ["Flask", "MySQL", "Docker"],
        "mobile": ["React Native", "Expo"],
    },
    "features": [
        "Feature one",
        "Feature two",
    ],
    "url": "https://my-project.example.com",
    "github": "https://github.com/you/my-project",
    "image": "assets/images/my-project/preview.png",
    "links": [
        {"name": "Admin Panel", "url": "https://my-project.example.com/admin", "icon": "fas fa-shield-alt"},
        {"name": "API Docs", "url": "https://my-project.example.com/docs", "icon": "fas fa-book"},
    ],
    "buttons": [],
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | yes | Display name |
| `subtitle` | yes | Client, employer, or context |
| `description` | yes | 2-3 sentence summary |
| `tech` | yes | `web` and `mobile` lists of tech tags |
| `features` | no | Bullet list of key features |
| `status` | no | Operational status tag (`operational` / `in progress` / `halted`) |
| `note` | no | Short note shown under the status tag (e.g. job update) |
| `url` | no | Live site URL (shows online/offline status) |
| `github` | no | Source repo link |
| `image` | no | Path relative to `static/` (shown on detail page) |
| `links` | no | Array of external links with icons |
| `buttons` | no | Action buttons (for API triggers) |

Place preview images in `static/assets/images/<slug>/`.

## Running

```bash
# Development on port 8000 with no auth to match Dockerfile EXPOSE 8000
DEPLOYMENT_TYPE=DEBUG python run.py

# Docker (app :8000 internal via Caddy :7011)
docker compose up --build
```

The Cloudflare tunnel ingress must point at the Caddy container
(`portfolio_caddy:7011`), not the app.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `DEPLOYMENT_TYPE` | yes | `DEBUG` or `PRODUCTION` |

## Ports

| Port | Service |
|------|---------|
| 8000 | App (granian ASGI, internal via `portfolio_main:8000` with Caddy on :7011) |
| 7011 | Caddy (loopback-bound for tunnel only) |
| 8005 | Documentation (granian, internal via Caddy) |

Portfolio's block is 7010; Caddy owns :7011, app is exposed internally as :8000 (Dockerfile `EXPOSE 8000`, `granian --interface asgi --port 8000 wsgi:app`, compose healthcheck `127.0.0.1:8000/health`, Caddy `reverse_proxy portfolio_main:8000`).

## Auth

This project is gated via the **wildcard** GateKeeper ingress. `gatekeeper_caddy:7000` on the shared `gatekeeper_dynamic` network checks `GET /api/authz/forward-auth` before Caddy proxies. The local `caddy/Caddyfile` has no per-app `forward_auth`; gating is at the apex wildcard (same as other gated apps on `gatekeeper_dynamic`). A valid `gatekeeper_token` cookie (or `?access_code=` magic link) passes; otherwise GateKeeper redirects to login. `/health` bypasses via GateKeeper rule.

See `compose.yaml`: `portfolio_caddy` joins `gatekeeper_dynamic` (external `gatekeeper_dynamic`), and `caddy/Caddyfile` proxies `portfolio_main:8000`/`portfolio_documentation:8005` without a local `forward_auth`.

## Errors

JS: `console.error({status, request_id, stack})` + toast; Server: structlog JSON + X-Request-ID to docker logs; envelope `{error:{code,message,request_id}}`. No traceback to client.

## Tests

```bash
uv run --no-project --with pytest --with-requirements requirements.txt \
  --with-requirements requirements-dev.txt pytest -q
```

The suite is a three-case smoke check — `/health` returns `{"status": "ok"}`, `/` renders HTML, and an unknown project slug returns 404. It asserts the app constructs and serves; it does not cover every route.
