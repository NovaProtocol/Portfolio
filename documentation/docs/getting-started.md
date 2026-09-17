# Getting Started

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Docker & Docker Compose | Latest | All services (recommended) |
| Python | >= 3.14 | Local development |
| Caddy (or tunnel) | 2-alpine | Reverse proxy / auth gate |

---

## 1. Clone & Configure

```bash
git clone https://github.com/NovaProtocol/Portfolio
cd Portfolio
```

Env vars are **injected by compose interpolation** with no `.env` file read. They are documented in `.env.example` (the source of truth):

| Variable | Required | Description | How injected |
|----------|----------|-------------|--------------|
| `DEPLOYMENT_TYPE` | yes | `DEBUG` or `PRODUCTION` | `${DEPLOYMENT_TYPE:?…}` in compose.yaml |
| `SECRET_KEY` | reserved | Session signing secret (future) | `${SECRET_KEY:-}` if consumed |

> Never `cp .env.example .env`. In production the deployment tool exports the vars; locally `export DEPLOYMENT_TYPE=DEBUG` then run.

Validate required vars:

```bash
docker compose config > /dev/null # fails fast on missing ${VAR:?}
```

---

## 2. Run Locally (dev, port 8000, no auth)

```bash
export DEPLOYMENT_TYPE=DEBUG
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
# → http://127.0.0.1:8000/
# → http://127.0.0.1:8000/health → {"status":"ok"}
# → http://127.0.0.1:8000/projects/
# → http://127.0.0.1:8000/resume/
```

`run.py` uses `argparse --mode debug/production` and runs `uvicorn apps:create_app --reload` in debug or `granian --interface asgi wsgi:app` in production, matching the actual `Dockerfile EXPOSE 8000` / compose healthcheck `127.0.0.1:8000/health` (see Dockerfile).

---

## 3. Run with Docker (app :8000 internal via Caddy :7011, gated at wildcard)

```bash
export DEPLOYMENT_TYPE=PRODUCTION
docker compose up -d --build
docker compose ps # health: portfolio_main (healthy)
curl -i http://127.0.0.1:7011/health # 200 with GateKeeper bypassed
curl -i http://127.0.0.1:7011/ # 302 → GateKeeper login (no cookie)
```

| URL | Result |
|-----|--------|
| `http://127.0.0.1:7011/health` | `{"status":"ok"}` via Caddy to `portfolio_main:8000` |
| `http://127.0.0.1:7011/documentation/` | via Caddy to `portfolio_documentation:8005` (wildcard-gated when fronted) |
| `http://127.0.0.1:7011/?access_code=<code>` | 302 + `Set-Cookie` → `gatekeeper_token`, param stripped → authed |

Prerequisite networks (run once):

```bash
docker network create gatekeeper # GateKeeper-owned; only gatekeeper_caddy joins the tunnel
```

---

## 4. Documentation Site

```bash
# Inside compose (gated at /documentation/*)
docker compose up -d --build documentation
# → http://127.0.0.1:7011/documentation/ (via Caddy; GateKeeper rules decide the gate)

# Direct access without the gate on the container network only
docker compose exec documentation curl -i http://127.0.0.1:8005/health # 200

# Local preview (no Docker)
pip install -r documentation/requirements.txt
mkdocs serve -f documentation/mkdocs.yml # http://127.0.0.1:8000
mkdocs build -f documentation/mkdocs.yml # builds documentation/site/
```

---

## 5. Development Workflow

```bash
# Formatting & lint (house: ruff line 100, double quotes, isort)
pip install ruff mypy
ruff format .
ruff check --fix .
mypy .

# Or via pre-commit (local only, no CI)
pre-commit run --all-files

# Validate compose
docker compose config > /dev/null

# Logs
docker compose logs -f app
docker compose logs --tail 100 caddy
docker compose logs -f documentation

# Rebuild one service
docker compose up -d --build --no-deps app

# Stop
docker compose down # keep volumes
docker compose down -v # also delete volumes (none for Portfolio)
```

---

## 6. Adding a Project

Add an entry to `PROJECTS` in `apps/projects/routes.py` (see README for the full schema), place its preview image under `static/assets/images/<slug>/`, then:

```bash
DEPLOYMENT_TYPE=DEBUG python run.py # verify /projects/ and /projects/info/<slug>/
```

No database and no migrations. Content lives in code and `data/resume.json`.
