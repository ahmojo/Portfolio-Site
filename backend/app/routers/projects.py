"""Projects router — proxies GitHub repo metadata with caching."""
from __future__ import annotations

from fastapi import APIRouter

from ..db import load_content
from ..github import get_projects
from ..models import ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects():
    content = load_content()
    projects = [
        (item.get("title", ""), item.get("repo", ""))
        for item in content.get("projects", [])
        if item.get("repo", "").strip()
    ]
    return await get_projects(projects)
