from __future__ import annotations

import io
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

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


def _portfolio_links() -> tuple[str, str]:
    contact = _RESUME.get("contact", {}) if isinstance(_RESUME, dict) else {}
    base = (contact.get("portfolio") or "").strip().rstrip("/")
    code = (contact.get("access_code") or "").strip()
    if not base or not code:
        return "", ""
    return f"{base}/?access_code={code}", f"{base} (access code: {code})"


def _resume_context(extra: dict | None = None) -> dict:
    magic_link, label = _portfolio_links()
    context: dict = {"resume": _RESUME, "portfolio_url": magic_link, "portfolio_label": label}
    if extra:
        context.update(extra)
    return context


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "resume/index.html", _resume_context())


@router.get("/qr.svg")
async def qr_svg():
    magic_link, _label = _portfolio_links()
    if not magic_link:
        raise HTTPException(status_code=404, detail="Not found")
    import segno

    qr = segno.make(magic_link)
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=10, border=2)
    return Response(
        content=buf.getvalue(),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )


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
