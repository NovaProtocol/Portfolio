from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from apps.data import PROJECTS, PROJECT_PRIORITY
from apps.templating import templates

router = APIRouter(prefix="/projects")


def ordered_projects() -> list[tuple[str, dict]]:
    """Active projects, highest priority first (the weight is never displayed)."""
    active = [(slug, p) for slug, p in PROJECTS.items() if p.get("active")]
    return sorted(active, key=lambda sp: PROJECT_PRIORITY.get(sp[0], 0), reverse=True)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "projects/index.html", {"projects": ordered_projects()})


@router.get("/info/{slug}/", response_class=HTMLResponse)
async def detail(request: Request, slug: str):
    project = PROJECTS.get(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return templates.TemplateResponse(request, "projects/detail.html", {"project": project, "slug": slug})
