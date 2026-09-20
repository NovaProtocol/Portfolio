# Caching

Every service in this repo sets `Cache-Control` from one middleware on the app
itself: `apps/middleware.py` for the portfolio site, and `documentation/cache.py`
for the docs service. There is no cache policy in a `Caddyfile` and none at the
edge, because the edge cannot tell which visitor a response belongs to.

## The rule

> A response may be `public`-cacheable only when the path is ungated (the gate
> resolved `action == "none"`) and the upstream chose that header itself.

The middleware decides in this order:

1. **An existing header is kept.** If the response already carries
   `Cache-Control`, it is returned untouched. A route that made a deliberate
   decision about its own content is not overruled by a deployment-type default.
2. **A gap is filled.** Only when the response carries none does the middleware
   write a value: `no-store` in debug, the path class's lifespan otherwise.

`config.DEBUG` decides *what value is filled in*. It never decides whether an
existing value is overwritten. Before this rule was fixed, the debug branch
assigned `no-store` unconditionally, which pinned every asset on a debug
deployment to no caching at all.

## Values

Portfolio site (`apps/middleware.py`):

| Class | Paths | `DEPLOYMENT_TYPE=DEBUG` | Production |
|-------|-------|------------------------|------------|
| Static | `/static/*` | `no-store` | `public, max-age=86400` |
| Health | `/health` | `no-store` | `public, max-age=3600` |
| HTML | everything else | `no-store` | `private, max-age=300` |

Docs service (`documentation/cache.py`):

| Class | Paths | Debug | Production |
|-------|-------|-------|------------|
| Static | `/static/` | `no-store` | `public, max-age=86400` |
| API | `/api/` | `no-store` | `private, no-store` |
| Health | `/health` | `no-store` | `public, max-age=3600` |
| HTML | everything else | `no-store` | `private, max-age=300` |

The classes are tested in that order, so an API prefix wins over the health list
and `/api/health` is `private, no-store`. The `"/api/health"` entry in the docs
copy's `_MISC_PATHS` therefore never reaches its own branch. Point a monitor at
`/health`.

The constants live at the top of each middleware and are deliberately not
environment variables: four integers do not justify new required config, and a
redeploy is the honest way to change them.

## The safety net

The gate is what makes "keep the upstream header" safe. GateKeeper demotes any
shared-cacheable value on a response it produced or on a proxied response whose
request it decided, so a gated route cannot publish a `public` page through the
gate. On this stack that happens before the response reaches Cloudflare, which is
a shared cache keyed on the URL alone.

The ungated pass-through is left alone. That is what lets a project publish an
asset on an `action == "none"` path and have it cached at the edge instead of
re-fetched on every embed.

Neither middleware in this repo is the gate: each keeps an upstream header and
does not demote. The gateway does that on the way out.

## Verifying a change

Read the header from the running service rather than from the source:

```bash
curl -sI http://127.0.0.1:7011/static/js/error.js | grep -i cache-control
```

A static path should show `public, max-age=86400` outside debug. A response that
shows exactly one `Cache-Control` line is correct; two lines mean something at
the edge is adding rather than replacing, which is always a defect.
