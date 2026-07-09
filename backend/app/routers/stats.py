"""GitHub stats router — contributions, streak, activity."""
from __future__ import annotations

from fastapi import APIRouter

from ..contributions import get_stats
from ..models import GithubStatsOut

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=GithubStatsOut)
async def github_stats():
    return await get_stats()
