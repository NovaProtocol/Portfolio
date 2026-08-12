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
| `status` | no | Operational status tag (`operational` / `halted`) |
| `note` | no | Short note shown under the status tag (e.g. job update) |
| `url` | no | Live site URL (shows online/offline status) |
| `github` | no | Source repo link |
| `image` | no | Path relative to `static/` (shown on detail page) |
| `links` | no | Array of external links with icons |
| `buttons` | no | Action buttons (for API triggers) |

Place preview images in `static/assets/images/<slug>/`.

## Running

```bash
# Development (port 7010, no auth)
DEPLOYMENT_TYPE=DEBUG python run.py

# Docker (app :7010 internal, Caddy :7011 exposed)
docker compose up --build
```

The Cloudflare tunnel ingress must point at the Caddy container
(`portfolio_caddy:7011`), not the app.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `DEPLOYMENT_TYPE` | yes | `DEBUG` or `PRODUCTION` |

## Auth

Every request through Caddy is checked against GateKeeper's forward-auth
endpoint (`/api/authz/forward-auth`). A valid `gatekeeper_token` cookie passes
(200). Without one, a valid `?access_code=` in the URL logs in on the spot and
is stripped from the URL. Otherwise the request is redirected to the GateKeeper
login page. Only `/health` bypasses the gate.

See `caddy/Caddyfile`: GateKeeper is reached as `gatekeeper:7000` over the
external `gatekeeper_default` Docker network.
