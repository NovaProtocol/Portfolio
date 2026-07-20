# Portfolio

Personal portfolio site built with Flask 3.1 + Gunicorn.

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
| `url` | no | Live site URL (shows online/offline status) |
| `github` | no | Source repo link |
| `image` | no | Path relative to `static/` (shown on detail page) |
| `links` | no | Array of external links with icons |
| `buttons` | no | Action buttons (for API triggers) |

Place preview images in `static/assets/images/<slug>/`.

## Running

```bash
# Development (port 7010)
python run.py --deployment_type DEBUG

# Production via gunicorn
python run.py --deployment_type PRODUCTION

# Docker
docker compose up --build
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `DEPLOYMENT_TYPE` | yes | `DEBUG` or `PRODUCTION` |
| `SECRET_KEY` | yes | Must match GateKeeper's key |
| `GATEKEEPER_INTERNAL` | yes | Internal URL for API calls (`http://gatekeeper:7000` in Docker) |

## Auth

Portfolio is protected by [GateKeeper](https://github.com/NovaProtocol/GateKeeper). Unauthenticated requests are redirected to the GateKeeper login page. The redirect URL is derived by swapping the subdomain to `gatekeeper` (e.g. `portfolio.example.com` → `gatekeeper.example.com`).
