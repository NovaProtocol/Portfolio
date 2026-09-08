from __future__ import annotations

from fastapi import APIRouter

from apps.routes.home import router as home_router
from apps.routes.projects import router as projects_router
from apps.routes.resume import router as resume_router

router = APIRouter()
router.include_router(home_router)
router.include_router(projects_router)
router.include_router(resume_router)
