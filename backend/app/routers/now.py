"""Now router — a single editable 'what I'm doing right now' status."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Header

from ..config import settings
from ..db import get_conn
from ..models import NowIn, NowOut

router = APIRouter(prefix="/api/now", tags=["now"])


@router.get("", response_model=NowOut)
def get_now():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT status, detail, updated_at FROM now_state WHERE id = 1"
        ).fetchone()
    if not row:
        return NowOut(status="", detail="", updated_at="")
    return NowOut(**dict(row))


@router.put("", response_model=NowOut)
def update_now(payload: NowIn, authorization: str = Header(default="")):
    # require token only if one is configured
    if settings.now_token:
        token = authorization.removeprefix("Bearer ").strip()
        if token != settings.now_token or not token:
            raise HTTPException(status_code=401, detail="Invalid or missing token.")

    with get_conn() as conn:
        conn.execute(
            "UPDATE now_state SET status = ?, detail = ?, updated_at = datetime('now') WHERE id = 1",
            (payload.status, payload.detail),
        )
        row = conn.execute(
            "SELECT status, detail, updated_at FROM now_state WHERE id = 1"
        ).fetchone()
    return NowOut(**dict(row))
