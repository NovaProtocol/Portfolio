from __future__ import annotations

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
