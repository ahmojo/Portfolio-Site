"""Site content router.

GET /api/content  -> public, returns the editable content blob.
PUT /api/content  -> admin-only, replaces the whole blob.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Response

from ..db import load_content, save_content
from ..models import SiteContent
from ..open_source import get_open_source, merge_open_source
from ..security import require_admin

router = APIRouter(prefix="/api/content", tags=["content"])

_content_version: str = "0"


@router.get("", response_model=SiteContent)
async def get_content(response: Response):
    response.headers["Cache-Control"] = "public, max-age=10"
    data = load_content()
    content = SiteContent.model_validate(data)
    live_items = await get_open_source()
    data["open_source"] = merge_open_source(
        live_items,
        [item.model_dump() for item in content.open_source],
        content.open_source_hidden,
    )
    return SiteContent.model_validate(data)

@router.put("", response_model=SiteContent, dependencies=[Depends(require_admin)])
def put_content(payload: SiteContent):
    data = payload.model_dump()
    save_content(data)
    global _content_version
    _content_version = str(int(time.time()))
    return SiteContent.model_validate(data)
