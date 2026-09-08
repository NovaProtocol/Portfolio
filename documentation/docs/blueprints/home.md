# Home Blueprint

**Module:** `apps/routes/home.py` — `APIRouter`

Serves the landing page and the public health probe.

## Routes

| Route | Handler | Description |
|-------|---------|-------------|
| `GET /` | `apps.routes.home.index` | Renders `home/index.html` — hero, project highlights, live embeds |
| `GET /health` | `apps.routes.home.health` | Returns `{"status":"ok"}` JSON — compose healthcheck and Caddy bypass |

```python
# apps/routes/home.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from apps.templating import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "home/index.html", {})

@router.get("/health")
async def health():
    return {"status": "ok"}
```

## Route Registration

Registered centrally in `apps/routes/__init__.py` and included in `apps/__init__.py:create_app()` via `app.include_router(router)`.

## Templates

- `apps/home/templates/home/index.html` extends `apps/templates/base.html` (the shared base all blueprints share).
- Static helpers from `apps/tags.py` supply clickable tech tags (`tech_tag()` returns a `Markup` anchor when the tag is known in `TAG_LINKS`).

## Caddy Wiring

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

Gate is at the **wildcard** (`gatekeeper_dynamic`) — local `Caddyfile` has no per-app `forward_auth` (see live `caddy/Caddyfile`). `/health` is the liveness probe; wildcard enforces `gatekeeper_token` / `?access_code=` before Caddy proxies.

## Healthcheck

Compose probes the FastAPI container directly (no Caddy hop):

```yaml
healthcheck:
 test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
 interval: 30s
 timeout: 5s
 retries: 3
 start_period: 10s
```

Manual:

```bash
curl http://127.0.0.1:8000/health          # direct (container network)
curl -i http://127.0.0.1:7011/health   # via Caddy, 200
```
