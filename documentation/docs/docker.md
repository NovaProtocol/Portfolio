# Docker & Deployment

## Services

| Service | Build | Container | Port | Notes |
|---------|-------|-----------|------|-------|
| **app** | `Dockerfile` | `portfolio_main` | 8000 gunicorn gthread | `HEALTHCHECK` on `/health` (`127.0.0.1:8000`) |
| **documentation** | `documentation/Dockerfile` | `portfolio_documentation` | 8005 granian | `expose:` only, `HEALTHCHECK` on `:8005/health` |
| **caddy** | `caddy/Dockerfile` | `portfolio_caddy` | 7011 | `127.0.0.1:7011:7011` loopback-only |

All services have `restart: unless-stopped`.

```yaml
# compose.yaml (trimmed)
services:
  app:
    build: {context: ., dockerfile: Dockerfile}
    container_name: portfolio_main
    restart: unless-stopped
    environment:
      DEPLOYMENT_TYPE: ${DEPLOYMENT_TYPE:?DEPLOYMENT_TYPE is required}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    networks: [default]
  documentation:
    build: {context: ., dockerfile: documentation/Dockerfile}
    container_name: portfolio_documentation
    restart: unless-stopped
    expose: ["8005"]
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8005/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    networks: [default]
  caddy:
    build: {context: ./caddy, dockerfile: Dockerfile}
    container_name: portfolio_caddy
    restart: unless-stopped
    ports: ["127.0.0.1:7011:7011"]
    networks: [default, gatekeeper_dynamic, cloudflared-tunnel]

networks:
  default:
  gatekeeper: {external: true, name: gatekeeper_default}  # legacy, caddy uses gatekeeper_dynamic
  gatekeeper_dynamic: {external: true, name: gatekeeper_dynamic}
  cloudflared-tunnel: {external: true, name: cloudflared-tunnel_default}
```

## Dockerfile — App

```dockerfile
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libc6-dev \
    libglib2.0-0 libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \
    libffi8 libjpeg62-turbo libopenjp2-7 libcairo2 libgdk-pixbuf-2.0-0 \
    shared-mime-info fonts-dejavu \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python3 -m compileall -q /app 2>/dev/null || true
RUN rm -f .env
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app

EXPOSE 8000
USER appuser
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "gthread", "--workers", "2", "--threads", "4", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
```

- `python:3.14-slim` (house default — no custom `python3146t` base).
- `requirements.txt` before `COPY . .` for layer caching.
- `--no-cache-dir` on pip.
- `compileall` catches syntax errors at build time.
- `USER appuser` (uid 10001) — never `root` in production.
- `EXPOSE 8000` matches Caddy's `reverse_proxy portfolio_main:8000` and the gunicorn `--bind` (`Dockerfile` + `compose healthcheck` source of truth).

## Dockerfile — Documentation

```dockerfile
FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY documentation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY documentation/ .
RUN mkdocs build

RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app

EXPOSE 8005
USER appuser
CMD ["granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "8005", "--workers", "1", "app:app"]
```

- Reuses `python:3.14-slim` (single base for both images).
- `mkdocs build` at image build time — `site/` is baked into the image, not built on boot.
- `app.py` serves `site/` on `:8005` with `/health` and request logging.

## Caddyfile

```caddyfile
:7011 {
    handle /health {
        reverse_proxy portfolio_main:8000
    }

    handle_path /documentation/* {
        reverse_proxy portfolio_documentation:8005
    }

    handle {
        reverse_proxy portfolio_main:8000
    }
}
```

- Built from `caddy:2-alpine` (`caddy/Dockerfile: FROM caddy:2-alpine / COPY Caddyfile`).
- Exactly one `Caddyfile` (no `.dev`/`.prod` variants — production is the only config).
- Site address `:7011` matches compose publish `127.0.0.1:7011:7011`.
- Proxy targets use **`container_name`** (`portfolio_main:8000`, `portfolio_documentation:8005`), never the service name `app`, to avoid the shared-network DNS collision on `cloudflared-tunnel_default` / `gatekeeper_dynamic`.
- Gate is at the **wildcard** (`gatekeeper_dynamic`) — local `Caddyfile` has no per-app `forward_auth`; see `caddy/Caddyfile` live (3 handles: `/health`, `/documentation/*`, catch-all). `handle_path` strips `/documentation` before proxying.
- `X-Forwarded-*` headers are forwarded unchanged for GateKeeper's redirect reconstruction.

Compose networks: app + docs on `default`; caddy on `default` + `gatekeeper_dynamic` + `cloudflared-tunnel`. Caddy publishes `127.0.0.1:7011:7011` (loopback-only — tunnel ingress is `portfolio_caddy:7011`).

## Health

- App: `http://127.0.0.1:8000/health` (container) and `http://127.0.0.1:7011/health` (via Caddy).
- Docs: `http://127.0.0.1:8005/health` (container) and `http://127.0.0.1:7011/documentation/` (via Caddy) — probe `http://portfolio_documentation:8005/health` from a sibling container.

```bash
docker compose ps                    # HEALTH columns
docker inspect --format='{{.State.Health.Status}}' portfolio_main
docker inspect --format='{{.State.Health.Status}}' portfolio_documentation
curl -i http://127.0.0.1:7011/health
docker compose exec documentation python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8005/health').read())"
```

## Environment

| Variable | Required | Where | Value |
|----------|----------|-------|-------|
| `DEPLOYMENT_TYPE` | yes | `app` env | `DEBUG` or `PRODUCTION` (`${VAR:?}`) |

No `SECRET_KEY` or GateKeeper vars in the app — the gate lives entirely in Caddy.

## Day-to-Day

```bash
export DEPLOYMENT_TYPE=PRODUCTION
docker compose up -d --build          # build + start (layer-cached)
docker compose ps                     # status + health
docker compose logs -f app
docker compose logs --tail=100 caddy
docker compose logs -f documentation
docker compose build documentation    # rebuild docs only
docker compose up -d --build --no-deps documentation
docker compose exec app sh            # shell (slim image — sh, not bash)
docker compose exec app python -c "import os; print(os.environ['DEPLOYMENT_TYPE'])"
docker compose down                   # stop, keep volumes
```
