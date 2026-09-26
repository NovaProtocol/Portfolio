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

DEFAULT_VARIANT = "mechanical"


def _order_projects(resume: dict, variant: str) -> dict:
    """The resume with `projects` in the order that variant asks for.

    `projects` in the data is the pool of project content, not a running order:
    each variant names the projects it wants and the order to put them in. A
    variant is therefore a projection of one file, so the two can never disagree
    about what a project says, and adding a third is a data change.

    A project named by a variant but missing from the pool is skipped rather than
    raised, because the alternative is a 500 on a resume.
    """
    spec = (resume.get("variants") or {}).get(variant) or {}
    order = spec.get("order")
    if not order:
        return resume

    by_name = {p.get("name"): p for p in resume.get("projects") or []}
    chosen = [by_name[name] for name in order if name in by_name]

    missing = [name for name in order if name not in by_name]
    if missing:
        logger.warning("resume variant %r names unknown projects: %s", variant, missing)

    return {**resume, "projects": chosen}


def _resume_context(variant: str = DEFAULT_VARIANT) -> dict:
    """Context for the resume templates.

    The template receives a resolved `projects` list and a `variant` name for the
    selector, so no template needs to know how variants work.
    """
    return {
        "resume": _order_projects(_RESUME, variant),
        "variant": variant,
        "variants": _RESUME.get("variants") or {},
    }


def _normalise_variant(name: str | None) -> str:
    """A known variant name, falling back to the default rather than erroring."""
    known = _RESUME.get("variants") or {}
    if name and name in known:
        return name
    return DEFAULT_VARIANT


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, variant: str = DEFAULT_VARIANT):
    return templates.TemplateResponse(
        request, "resume/index.html", _resume_context(_normalise_variant(variant))
    )


@router.get("/view", response_class=HTMLResponse)
async def view(request: Request, page: int | None = None, variant: str = DEFAULT_VARIANT):
    """One sheet, or both in one document, for one variant.

    There is no `theme` parameter. There were three themes behind a selector on
    the resume page; the selector is gone, so accepting the argument would only
    offer a reader a way to render a variant nothing points at. The old values
    are ignored rather than rejected, so a bookmarked `?theme=2` still renders.
    """
    resolved = _normalise_variant(variant)
    if page is not None:
        mapping = {1: "resume/page1.html", 2: "resume/page2.html"}
        template = mapping.get(page)
        if not template:
            raise HTTPException(status_code=404, detail="Not found")
        return templates.TemplateResponse(
            request, template, _resume_context(resolved)
        )
    return templates.TemplateResponse(
        request, "resume/view.html", _resume_context(resolved)
    )
