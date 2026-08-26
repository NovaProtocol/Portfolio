# Documentation

Full project documentation for **Portfolio**, built with [MkDocs](https://www.mkdocs.org/) and the Material theme.

## Contents

| Section | Description |
|---------|-------------|
| [Home](docs/index.md) | Project overview, stack, and routes |
| [Getting Started](docs/getting-started.md) | Prerequisites and startup |
| [Architecture](docs/architecture.md) | App factory, blueprints, request flow |
| [Blueprints](docs/blueprints/home.md) | Home, Projects, Resume blueprints |
| [Templates & Static](docs/templates-static.md) | Jinja2 and static assets |
| [Docker](docs/docker.md) | Compose, Dockerfile, Caddy, GateKeeper |

## Building Locally

```bash
pip install -r requirements.txt
mkdocs build
mkdocs serve    # preview at http://localhost:8000
```

Served in production as `portfolio_documentation:8005` via FastAPI + granian, gated at `/documentation/*`.
