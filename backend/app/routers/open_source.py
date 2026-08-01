"""Public endpoint for automatically discovered merged pull requests."""
from __future__ import annotations

from fastapi import APIRouter, Response

from ..models import OpenSourceItem
from ..open_source import get_open_source

router = APIRouter(prefix="/api/open-source", tags=["open source"])


@router.get("", response_model=list[OpenSourceItem])
async def merged_pull_requests(response: Response):
    response.headers["Cache-Control"] = (
        "public, max-age=600, stale-while-revalidate=3600"
    )
    return await get_open_source()
