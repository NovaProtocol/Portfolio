from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from apps.templating import templates

router = APIRouter(prefix="/resume")

_DATA = Path(__file__).resolve().parent.parent.parent / "data"
_DEFAULT_PATH = _DATA / "default_resume.json"
_OVERWRITE_PATH = _DATA / "overwrite_resume.json"

# The resume every other resume is built from, and the one served when nothing
# else is asked for. It is the general-purpose one: it has to read for a
# recruiter who did not say what they were hiring for.
DEFAULT_RESUME = "Generic"

logger = logging.getLogger(__name__)


def _read_json(path: Path, fallback: Any) -> Any:
    """Parse a JSON file, logging and falling back rather than raising.

    A malformed file must not take the site down: the resume is one page of it,
    and the rest of the site still has something to say.
    """
    try:
        return json.loads(path.read_text())
    except OSError:
        logger.exception("Could not read %s", path)
    except json.JSONDecodeError:
        logger.exception("%s is not valid JSON", path)
    return fallback


def _deep_merge(base: dict, override: dict) -> dict:
    """`override` over `base`, recursively, without mutating either.

    Recursive because an override that sets `education[0].awards` must not drop
    the rest of that education entry. Lists are **replaced**, not merged: a
    shorter `projects` list is a deliberate choice about what to show, and
    concatenating would instead produce a resume the author never wrote.
    """
    out = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(value, dict)
        ):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _expand_projects(resume: dict) -> dict:
    """Replace each project named in a list with the project itself.

    An override names projects by name so that its text lives in one place. The
    content of every project is in `default_resume.json`, and a named resume that
    repeats it would be a second copy to keep in step.
    """
    projects = resume.get("projects")
    if not isinstance(projects, list) or not all(isinstance(p, str) for p in projects):
        return resume

    pool = resume.get("project_pool") or []
    by_name = {p.get("name"): p for p in pool}
    chosen = []
    for name in projects:
        if name in by_name:
            chosen.append(copy.deepcopy(by_name[name]))
        else:
            logger.warning("resume names a project that does not exist: %r", name)
    return {**resume, "projects": chosen}


def _load_resumes() -> tuple[dict[str, dict], list[dict]]:
    """Every resume keyed by name, and the list of names to offer.

    Built once at import: the files ship inside the image, so there is nothing to
    pick up at runtime that a restart would not also pick up.
    """
    default = _read_json(_DEFAULT_PATH, {})
    if not default:
        return {}, []

    entries = _read_json(_OVERWRITE_PATH, [])
    if not isinstance(entries, list):
        logger.error("%s should hold a list of resumes", _OVERWRITE_PATH)
        entries = []

    # The pool is the default's own project content. A named resume names projects
    # from it rather than repeating their text, so a project is written once no
    # matter how many resumes show it.
    pool = default.get("projects") or []
    described = {
        d.get("name"): d for d in (default.get("resumes") or []) if isinstance(d, dict)
    }

    resumes: dict[str, dict] = {}
    listing: list[dict] = []

    resumes[DEFAULT_RESUME] = _expand_projects({**default, "project_pool": pool})
    generic = described.get(DEFAULT_RESUME) or {}
    listing.append({
        "name": DEFAULT_RESUME,
        "label": generic.get("label") or "Generic",
        "blurb": generic.get("blurb") or "General purpose. Reads for any role.",
    })

    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("resume_name"):
            logger.warning("an override has no resume_name; skipping it")
            continue
        name = entry["resume_name"]
        if name in resumes:
            logger.warning("two resumes are named %r; keeping the first", name)
            continue
        merged = _deep_merge(
            {**default, "project_pool": pool}, entry.get("overwrites") or {}
        )
        resumes[name] = _expand_projects(merged)
        # A label and blurb can live on the override itself, which is where a
        # reader adding a resume will look for them, or in the default's
        # `resumes` list for a name the default already knew about.
        note = described.get(name) or {}
        listing.append({
            "name": name,
            "label": entry.get("label") or note.get("label") or name,
            "blurb": entry.get("blurb") or note.get("blurb") or "",
        })

    return resumes, listing


_LOADED, _RESUME_LIST = _load_resumes()


def resume_names() -> list[str]:
    """Every resume name, in the order they are offered."""
    return [item["name"] for item in _RESUME_LIST]


def load_resume(name: str | None = None) -> dict:
    """One resolved resume, by name, defaulting to the generic one.

    Public because `tools/resume_fit.py` measures the same content the site
    serves. It used to keep its own copy of the ordering logic, which is a fill
    figure measured against a different document than the one published.
    """
    return _LOADED.get(name or DEFAULT_RESUME) or _LOADED.get(DEFAULT_RESUME) or {}


def _resume_context(name: str = DEFAULT_RESUME) -> dict:
    """Context for the resume templates.

    The template receives one resolved resume, its name, and the list to build a
    selector from. No template needs to know how an override is merged.
    """
    resume = _LOADED.get(name) or _LOADED.get(DEFAULT_RESUME) or {}
    return {
        "resume": resume,
        "resume_name": name,
        "resumes": _RESUME_LIST,
    }


def _normalise_resume(name: str | None) -> str:
    """A known resume name, falling back to the default rather than erroring.

    A stale bookmark or a typo should serve the generic resume, not a 500.
    """
    if name and name in _LOADED:
        return name
    return DEFAULT_RESUME


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, resume: str = DEFAULT_RESUME):
    return templates.TemplateResponse(
        request, "resume/index.html", _resume_context(_normalise_resume(resume))
    )


@router.get("/view", response_class=HTMLResponse)
async def view(request: Request, page: int | None = None, resume: str = DEFAULT_RESUME):
    """One sheet, or both in one document, for one resume.

    `?variant=` is the old name for this parameter and is ignored rather than
    rejected, so a link made before the resumes were named still renders.
    `?theme=` is from a time when the resume had three visual themes; it is
    ignored too, for the same reason.
    """
    resolved = _normalise_resume(resume)
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
