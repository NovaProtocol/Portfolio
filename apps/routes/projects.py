from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from apps.data import PROJECTS
from apps.templating import templates

router = APIRouter(prefix="/projects")


def ordered_projects() -> list[tuple[str, dict]]:
    return [(slug, project) for slug, project in PROJECTS.items() if project.get("active")]


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "projects/index.html", {"projects": ordered_projects()})


@router.get("/info/{slug}/", response_class=HTMLResponse)
async def detail(request: Request, slug: str):
    project = PROJECTS.get(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return templates.TemplateResponse(request, "projects/detail.html", {"project": project, "slug": slug})
