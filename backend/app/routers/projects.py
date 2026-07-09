"""Projects router — proxies GitHub repo metadata with caching."""
from __future__ import annotations

from fastapi import APIRouter

from ..github import get_projects
from ..models import ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects():
    return await get_projects()
