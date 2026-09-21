from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

try:
    import structlog.contextvars as _ctx  # type: ignore

    _HAS_STRUCTLOG = True
except ImportError:
    _HAS_STRUCTLOG = False

# Production cache lifespans, in seconds. Tuning one is a one-line edit here
# plus a redeploy; they are deliberately not env vars.
_STATIC_MAX_AGE = 86400
_HTML_MAX_AGE = 300
_MISC_MAX_AGE = 3600

# Debug value: forbids any cache from storing the response at all, so gated
# bytes never rest on shared infrastructure.
_NO_STORE = "no-store"

# Directives that already forbid a shared cache from storing the response.
# Debug keeps such a value rather than rewriting it.
_VISITOR_SCOPED = ("private", "no-store")

# Path classes. Anything unmatched falls through to the short HTML lifespan.
_STATIC_PREFIX = "/static/"
_API_PREFIXES = ("/api/",)
_MISC_PATHS = frozenset({"/health"})


def _public_max_age(seconds: int) -> str:
    return f"public, max-age={seconds}"


def _cache_control_for(path: str) -> str:
    if path.startswith(_STATIC_PREFIX):
        return _public_max_age(_STATIC_MAX_AGE)
    if path.startswith(_API_PREFIXES):
        # The app serves no API today, but the rule is stated anyway: an API
        # answer is per-visitor and may be gated, so a shared cache must never
        # hold one. Without this branch a future `/api/` route would inherit the
        # HTML lifespan below.
        return "private, no-store"
    if path in _MISC_PATHS:
        return _public_max_age(_MISC_MAX_AGE)
    return f"private, max-age={_HTML_MAX_AGE}"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        if _HAS_STRUCTLOG:
            try:
                _ctx.bind_contextvars(request_id=request_id)
            except Exception:
                pass
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            existing = response.headers.get("Access-Control-Expose-Headers", "")
            expose = "X-Request-ID"
            if existing:
                parts = {part.strip() for part in existing.split(",") if part.strip()}
                parts.add(expose)
                response.headers["Access-Control-Expose-Headers"] = ", ".join(sorted(parts))
            else:
                response.headers["Access-Control-Expose-Headers"] = expose
            return response
        finally:
            if _HAS_STRUCTLOG:
                try:
                    _ctx.unbind_contextvars("request_id")
                except Exception:
                    pass


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Set Cache-Control per deployment type, without overriding a route's own.

    Caching is a production behaviour. With ``is_debug`` set, anything
    shared-cacheable is replaced with ``no-store``, so a deliberately ``public``
    value never survives into a development deployment; a value that already
    forbids storage is kept verbatim. In production a response that already
    carries a ``Cache-Control`` header keeps it, and only a response with none
    is given the path class's lifespan.

    The invariant that makes keeping a header safe:

        A response may be ``public``-cacheable only when the path is ungated
        (the gate resolved ``action == "none"``) **and** the upstream chose
        that header itself.

    This service is not the gate, so it cannot know whether a path was gated and
    it does not demote. On a stack behind GateKeeper the gateway applies that
    demotion before the response reaches a shared cache.
    """

    def __init__(self, app: ASGIApp, is_debug: bool) -> None:
        super().__init__(app)
        self.is_debug = is_debug

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if self.is_debug:
            # `DEPLOYMENT_TYPE=debug` disables caching outright: nothing this
            # service hands out may be stored, whatever the upstream asked for.
            # Every lifespan below is a production behaviour. A value that
            # already forbids storage is kept verbatim so the gate's own
            # `private, no-store` survives; anything else, including a
            # deliberately `public` one, is replaced.
            value = response.headers.get("Cache-Control")
            if not value or not any(d in value for d in _VISITOR_SCOPED):
                response.headers["Cache-Control"] = _NO_STORE
            return response
        if "Cache-Control" in response.headers:
            return response
        response.headers["Cache-Control"] = _cache_control_for(request.url.path)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; connect-src 'self'; "
            "frame-src 'self' https://*.projectnova.download; "
            "frame-ancestors 'self' https://*.projectnova.download"
        )
        return response
