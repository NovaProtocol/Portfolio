from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from apps.templating import templates

router = APIRouter(prefix="/resume")

_RESUME_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "resume.json"

logger = logging.getLogger(__name__)


def _load_resume() -> dict:
    try:
        return json.loads(_RESUME_PATH.read_text())  # type: ignore[no-any-return]
    except (OSError, json.JSONDecodeError):
        logger.exception("Failed to load resume data from %s", _RESUME_PATH)
        return {}


_RESUME = _load_resume()

_THEMES = {1, 2, 3}


def _resume_context(extra: dict | None = None) -> dict:
    context: dict = {"resume": _RESUME}
    if extra:
        context.update(extra)
    return context


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "resume/index.html", _resume_context())


@router.get("/view", response_class=HTMLResponse)
async def view(request: Request, page: int | None = None, theme: int = 3):
    if theme not in _THEMES:
        theme = 3
    if page is not None:
        mapping = {1: "resume/page1.html", 2: "resume/page2.html"}
        template = mapping.get(page)
        if not template:
            raise HTTPException(status_code=404, detail="Not found")
        return templates.TemplateResponse(request, template, _resume_context({"theme": theme}))
    return templates.TemplateResponse(
        request, "resume/view.html", _resume_context({"theme": theme})
    )
