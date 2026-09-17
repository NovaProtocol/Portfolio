from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from apps.config import get_config

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    import structlog  # type: ignore

    _HAS_STRUCTLOG = True
except ImportError:
    _HAS_STRUCTLOG = False


def _configure_logging() -> None:
    if _HAS_STRUCTLOG:
        try:
            import structlog

            structlog.configure(
                processors=[
                    structlog.contextvars.merge_contextvars,
                    structlog.processors.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.JSONRenderer(),
                ],
                wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
                context_class=dict,
                logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
                cache_logger_on_first_use=True,
            )
            return
        except Exception:
            pass
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


def create_app() -> FastAPI:
    _configure_logging()
    config = get_config()

    app = FastAPI(
        title="Portfolio",
        description="Personal portfolio site",
        debug=config.DEBUG,
    )

    from apps.middleware import (
        CacheControlMiddleware,
        RequestIDMiddleware,
        SecurityHeadersMiddleware,
    )

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CacheControlMiddleware, is_debug=config.DEBUG)

    static_dir = _PROJECT_ROOT / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    from apps.errors import install_error_handlers
    from apps.routes import router
    from apps.templating import templates

    app.include_router(router)
    install_error_handlers(app, templates)

    return app
