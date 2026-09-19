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

# Path classes. Anything unmatched falls through to the short HTML lifespan.
_STATIC_PREFIX = "/static/"
_MISC_PATHS = frozenset({"/robots.txt", "/health"})


def _public_max_age(seconds: int) -> str:
    return f"public, max-age={seconds}"


def _cache_control_for(path: str) -> str:
    if path.startswith(_STATIC_PREFIX):
        return _public_max_age(_STATIC_MAX_AGE)
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
    """Set Cache-Control per deployment type: no-store in debug, lifespans otherwise."""

    def __init__(self, app: ASGIApp, is_debug: bool) -> None:
        super().__init__(app)
        self.is_debug = is_debug

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if self.is_debug:
            response.headers["Cache-Control"] = _NO_STORE
        elif "Cache-Control" not in response.headers:
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
