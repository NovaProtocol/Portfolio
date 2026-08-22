# Home Blueprint

**Module:** `apps/home/` — `home_blueprint`, `url_prefix=""`

Serves the landing page and the public health probe.

## Routes

| Route | Handler | Description |
|-------|---------|-------------|
| `GET /` | `apps.home.routes.index` | Renders `home/index.html` — hero, project highlights, live embeds |
| `GET /health` | `apps.home.routes.health` | Returns `{"status":"ok"}` JSON — compose healthcheck and Caddy bypass |

```python
# apps/home/routes.py
from __future__ import annotations

from flask import jsonify, render_template

from apps.home import blueprint


@blueprint.route("/")
def index():
    return render_template("home/index.html")


@blueprint.route("/health")
def health():
    return jsonify({"status": "ok"})
```

## Blueprint Registration

```python
# apps/home/__init__.py
from flask import Blueprint

blueprint = Blueprint(
    "home_blueprint",
    __name__,
    url_prefix="",
    template_folder="templates",
)
```

Registered centrally in `apps/__init__.py:register_blueprints()` via `import_module("apps.{}.routes".format(name))`.

## Templates

- `apps/home/templates/home/index.html` extends `apps/templates/base.html` (the shared base all blueprints share).
- Static helpers from `apps/tags.py` supply clickable tech tags (`tech_tag()` returns a `Markup` anchor when the tag is known in `TAG_LINKS`).

## Caddy Wiring

```caddyfile
:7011 {
    handle /health {
        reverse_proxy portfolio_main:7010
    }
    handle {
        forward_auth gatekeeper:7000 { uri /api/authz/forward-auth }
        reverse_proxy portfolio_main:7010
    }
}
```

`/health` is intentionally **ungated** so `docker compose ps` / tunnel probes succeed without a cookie.

## Healthcheck

Compose probes the Flask container directly (no Caddy hop):

```yaml
healthcheck:
 test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7010/health')"]
 interval: 30s
 timeout: 5s
 retries: 3
 start_period: 10s
```

Manual:

```bash
curl http://127.0.0.1:7010/health          # direct (container network)
curl -i http://127.0.0.1:7011/health   # via Caddy, 200 without auth
```
