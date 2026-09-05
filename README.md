# Portfolio

Personal portfolio site built with Flask 3.1 + Gunicorn, served behind a Caddy reverse proxy that gates access through [GateKeeper](https://github.com/NovaProtocol/GateKeeper).

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
# Development (port 8000, no auth — matches Dockerfile EXPOSE 8000)
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
| 8000 | App (gunicorn, internal — via `portfolio_main:8000`; Caddy :7011) |
| 7011 | Caddy (loopback-bound — tunnel only) |
| 8005 | Documentation (granian, internal — via Caddy) |

Portfolio's block is 7010; Caddy owns :7011, app is exposed internally as :8000 (Dockerfile `EXPOSE 8000`, `gunicorn --bind 0.0.0.0:8000`, compose healthcheck `127.0.0.1:8000/health`, Caddy `reverse_proxy portfolio_main:8000`).

## Auth

This project is gated via the **wildcard** GateKeeper ingress — `gatekeeper_caddy:7000` on the shared `gatekeeper_dynamic` network checks `GET /api/authz/forward-auth` before Caddy proxies. The local `caddy/Caddyfile` has no per-app `forward_auth`; gating is at the apex wildcard (same as other gated apps on `gatekeeper_dynamic`). A valid `gatekeeper_token` cookie (or `?access_code=` magic link) passes; otherwise GateKeeper redirects to login. `/health` bypasses via GateKeeper rule.

See `compose.yaml`: `portfolio_caddy` joins `gatekeeper_dynamic` (external `gatekeeper_dynamic`), and `caddy/Caddyfile` proxies `portfolio_main:8000`/`portfolio_documentation:8005` without a local `forward_auth`.
