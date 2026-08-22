# Why No gRPC

Portfolio has **no gRPC server, no `.proto` files, and no `api:50051`** — by design.

## House Rule (`reference/fastapi/grpc.md`)

> Use gRPC for container-to-container server-side traffic only. The API runs `grpc.aio.server` on `api:50051`; other containers call it with `grpc.aio.insecure_channel("api:50051")`. If you have no server-side container-to-container calls, skip gRPC entirely.

| Traffic | Protocol | Endpoint |
|---------|----------|----------|
| `api:50051` internal (worker → api, portal → api) | gRPC | `grpc.aio.server` |
| Browser / webhook / public via Caddy → api | HTTP | `handle /api/*` + `reverse_proxy api:8008` |

`50051` is `expose:` only, never `ports:`-published, on an `internal: true` network.

## Why Portfolio Needs None of It

Portfolio is a **single-service Flask monolith (modular but single container)** — the distinction matters:

- **Modular** refers to *code organization*: `apps/` has three sector blueprints (`home`, `projects`, `resume`) that share a `create_app()` factory. They are not separate deployables — they run in **one** `portfolio_main:7010` container via `gunicorn wsgi:app`.
- **Single-service** refers to *deployment*: one Flask app serves every route (`/`, `/health`, `/projects/*`, `/resume/*`, `/static/*`) on one port. There is no `api` container + `portal` container pair that would benefit from typed protos or streaming.
- The `documentation` service (`portfolio_documentation:8005`) is read-only MkDocs — stateless, builds `site/` at image-build time, serves prebuilt HTML, never calls Portfolio and is never called by it. No RPC in either direction.
- The only integration is **Caddy `forward_auth`** — an HTTP GET to `gatekeeper:7000 /api/authz/forward-auth` over the `gatekeeper_default` Docker network with `X-Forwarded-*` headers. That traffic is HTTP by contract; gRPC over HTTP/2 would require a dedicated gRPC gateway that the house Caddy does not do.
- All data is in-process: `PROJECTS` dict in `apps/projects/routes.py` and `data/resume.json` loaded once at import. No service boundary to serialize across.

Adding a `grpc.aio.server` on `:50051` would:

- Require `grpcio>=1.60,<2`, `grpcio-tools>=1.60,<2`, `protobuf>=4,<7` in `requirements.txt` with no caller.
- Introduce `.proto` compilation (`shared/proto/`, `proto_gen/`) and stubs that nothing imports.
- Publish `expose: ["50051"]` that is never probed — noise in compose and docs.
- Force `handle /api/*` thinking where none exists — Portfolio has no JSON API, only server-rendered HTML behind Caddy.
- Duplicate logic: the same `PROJECTS` lookup would be exposed over two transports for zero benefit.

## What We Document Instead

- **HTTP is the only contract:** browser `GET /`, `GET /projects/info/<slug>/`, `GET /resume/view`, `GET /static/...`, and the public `GET /health`. All go through Caddy `reverse_proxy portfolio_main:7010` (or `portfolio_documentation:8005` for docs via `handle_path`).
- **No service token**, no `X-Internal-API-Key`, no `API_INTERNAL_URL` / `API_GRPC_ADDR` — those vars belong to multi-service systems (WBS, SolveSpace).
- **GateKeeper** is the only auth — `forward_auth` at the edge; the Flask app holds no auth code.

## What a Future Split Would Look Like

If this monolith ever grew a second container that needed server-side calls (e.g., a dedicated search index, a sidecar that tail-calls the app for render jobs, or a `shared/` library extracted because the docs site started calling the app), the addition would be:

- `shared/proto/portfolio.proto` + `shared/proto_gen/` (generated `_pb2.py` / `_pb2_grpc.py`)
- `grpc.aio.server` on `api:50051` started in the Flask app's lifespan (or alongside `gunicorn` via a small `grpc_server.py` entrypoint)
- `grpc.aio.insecure_channel("api:50051")` from the new container on an `internal: true` `net-api` network
- `expose: ["50051"]` only (never `ports:`), business logic in `*_service.py` called by both the Flask routes and the gRPC servicers — per `reference/fastapi/grpc.md` lifespan pattern

Until then, this page is the evidence that **no gRPC** is the correct, documented decision — not an omission.

## Comparison: When gRPC Is Required

| System | Needs gRPC | Reason |
|--------|------------|--------|
| Portfolio | **No** — Flask monolith, modular but single container | One `portfolio_main:7010` serves every blueprint; docs is stateless |
| GateKeeper | **No** — Flask monolith | One `app.py` serves every route; docs is stateless |
| BuddysFreelanceProject | **No** — FastAPI monolith | `data/` inside the app, Caddy → app HTTP |
| NovaProtocol | **No** — FastAPI monolith | SVG renderers in-process, Caddy → app HTTP |
| WaterBillingSystem | **Yes** | `worker`/`portal`/`webhook` → `api:50051` over `net-api` |
| SolveSpace `executor/` | **Yes** | `api` → `executor:50051` (sandbox) |

```
[Internet] --HTTP--> [Caddy :7011] --HTTP--> [portfolio_main:7010 Flask gunicorn]
                                   --HTTP--> [portfolio_documentation:8005 FastAPI granian]
[ GateKeeper :7000 ] <--HTTP forward_auth-- [Caddy]  (HTTP only, no gRPC)
(no shared/proto, no 50051, no internal RPC)
```
