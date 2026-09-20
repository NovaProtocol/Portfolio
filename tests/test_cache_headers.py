"""Cache-Control precedence in ``apps/middleware.py`` and ``documentation/cache.py``.

The app and the documentation service each carry their own copy of the
middleware, so each is checked here. They share one promise: a response that
sets its own ``Cache-Control`` keeps it, and only a response that sets none is
given the deployment's answer.

The reason it matters is the site sits behind GateKeeper. While the precedence
was wrong, a resource that deliberately published its own lifespan was pinned to
``no-store`` on every request, which is what made caching impossible anywhere on
the deployment.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

UPSTREAM_CACHE = "public, max-age=300"


def load(path: str, name: str) -> Any:
    """Load the docs copy by path, because both modules are named ``cache``/``middleware``."""
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


from apps.middleware import CacheControlMiddleware as AppMiddleware  # noqa: E402

DOCS_CACHE = load("documentation/cache.py", "portfolio_docs_cache")

COPIES = [
    pytest.param(AppMiddleware, id="apps"),
    pytest.param(DOCS_CACHE.CacheControlMiddleware, id="documentation"),
]


def build(
    middleware: Any, is_debug: bool, headers: dict[str, str] | None = None, path: str = "/thing"
) -> FastAPI:
    app = FastAPI()

    @app.get(path)
    async def _route() -> PlainTextResponse:
        return PlainTextResponse("ok", headers=dict(headers or {}))

    app.add_middleware(middleware, is_debug=is_debug)  # type: ignore[arg-type]
    return app


@pytest.mark.parametrize("middleware", COPIES)
@pytest.mark.parametrize("is_debug", [True, False])
def test_a_response_that_sets_its_own_policy_keeps_it(middleware: Any, is_debug: bool) -> None:
    """The precedence fix itself, in both deployment modes."""
    with TestClient(build(middleware, is_debug, {"Cache-Control": UPSTREAM_CACHE})) as client:
        response = client.get("/thing")

    assert response.headers["Cache-Control"] == UPSTREAM_CACHE


@pytest.mark.parametrize("middleware", COPIES)
@pytest.mark.parametrize("is_debug", [True, False])
def test_a_response_with_no_policy_is_filled_in(middleware: Any, is_debug: bool) -> None:
    with TestClient(build(middleware, is_debug)) as client:
        response = client.get("/thing")

    expected = "no-store" if is_debug else "private, max-age=300"
    assert response.headers["Cache-Control"] == expected


@pytest.mark.parametrize("middleware", COPIES)
@pytest.mark.parametrize("is_debug", [True, False])
def test_a_static_path_is_public_in_production(middleware: Any, is_debug: bool) -> None:
    with TestClient(build(middleware, is_debug, path="/static/app.css")) as client:
        response = client.get("/static/app.css")

    expected = "no-store" if is_debug else "public, max-age=86400"
    assert response.headers["Cache-Control"] == expected


@pytest.mark.parametrize("middleware", COPIES)
@pytest.mark.parametrize("is_debug", [True, False])
def test_health_keeps_a_public_lifespan_in_production(middleware: Any, is_debug: bool) -> None:
    with TestClient(build(middleware, is_debug, path="/health")) as client:
        response = client.get("/health")

    expected = "no-store" if is_debug else "public, max-age=3600"
    assert response.headers["Cache-Control"] == expected


@pytest.mark.parametrize("is_debug", [True, False])
def test_the_docs_service_keeps_api_paths_private_in_production(is_debug: bool) -> None:
    """The app class has no API prefix, the docs copy does.

    Per-visitor docs queries may never rest in a shared cache, so the docs copy
    answers them with the literal ``private, no-store`` rather than a lifespan.
    """
    app = build(DOCS_CACHE.CacheControlMiddleware, is_debug, path="/api/pages")
    with TestClient(app) as client:
        response = client.get("/api/pages")

    value = response.headers["Cache-Control"]
    assert value == ("no-store" if is_debug else "private, no-store")
    assert "public" not in value


def test_the_documented_lifespans_match_the_constants() -> None:
    """The caching page quotes these numbers, so a change here breaks it.

    The page is ``documentation/docs/caching.md``. This test is the tripwire
    between it and the code.
    """
    from apps import middleware as app_middleware

    assert app_middleware._STATIC_MAX_AGE == 86400
    assert app_middleware._HTML_MAX_AGE == 300
    assert app_middleware._MISC_MAX_AGE == 3600

    assert DOCS_CACHE._STATIC_MAX_AGE == 86400
    assert DOCS_CACHE._HTML_MAX_AGE == 300
    assert DOCS_CACHE._MISC_MAX_AGE == 3600
