"""Public submission and admin-only reading of private portfolio feedback."""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
import unicodedata
from collections import OrderedDict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from .. import db, feedback_storage
from ..config import settings
from ..models import FeedbackIn, FeedbackSubmitOut, FeedbackSummaryOut
from ..privacy import _is_trusted_proxy, daily_visitor_hash, resolve_client_ip
from ..security import require_admin

router = APIRouter(prefix="/api/feedback", tags=["feedback"])
log = logging.getLogger("portfolio.feedback")

FEEDBACK_RATE_LIMIT = 3
FEEDBACK_RATE_WINDOW_SECONDS = 60 * 60
_ALLOWED_FETCH_SITES = {"same-origin", "same-site"}
_ALLOWED_FETCH_MODES = {"cors", "same-origin"}
_MAX_COMMENT_LENGTH = 1000


class FeedbackRateLimiter:
    """Bounded in-memory limiter for the single-worker public endpoint."""

    def __init__(self, max_keys: int = 4096) -> None:
        self._events: OrderedDict[str, deque[float]] = OrderedDict()
        self._max_keys = max_keys
        self._lock = threading.Lock()

    def allow(self, key: str, *, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events.get(key)
            if events is None:
                if len(self._events) >= self._max_keys:
                    self._events.popitem(last=False)
                events = deque()
                self._events[key] = events
            else:
                self._events.move_to_end(key)
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


feedback_rate_limiter = FeedbackRateLimiter()


def _clean_comment(value: str) -> str:
    """Normalize plain text and remove invisible control characters."""
    normalized = unicodedata.normalize("NFKC", value)
    return "".join(
        char
        for char in normalized
        if char in "\r\n\t" or not unicodedata.category(char).startswith("C")
    ).strip()


def _request_is_same_origin(request: Request) -> bool:
    origin = request.headers.get("origin", "").strip().rstrip("/").lower()
    if origin:
        if origin == "null":
            return not settings.is_production
        allowed = {
            str(item).strip().rstrip("/").lower()
            for item in settings.allowed_origins
            if str(item).strip() and str(item).strip() != "null"
        }
        canonical_origin = (
            f"{'https' if settings.is_production else request.url.scheme}://"
            f"{settings.analytics_hostname}"
        ).lower().rstrip("/")
        request_origin = f"{request.url.scheme}://{request.url.netloc}".lower().rstrip("/")
        same_local_origin = not settings.is_production and origin == request_origin
        if origin not in allowed and origin != canonical_origin and not same_local_origin:
            return False

    fetch_site = request.headers.get("sec-fetch-site", "").lower()
    fetch_mode = request.headers.get("sec-fetch-mode", "").lower()
    fetch_dest = request.headers.get("sec-fetch-dest", "").lower()
    return bool(
        (not fetch_site or fetch_site in _ALLOWED_FETCH_SITES)
        and (not fetch_mode or fetch_mode in _ALLOWED_FETCH_MODES)
        and (not fetch_dest or fetch_dest == "empty")
    )


def _feedback_key(request: Request) -> tuple[str, bool]:
    peer_ip = request.client.host if request.client else ""
    trusted_proxy = _is_trusted_proxy(peer_ip, settings.trusted_proxy_cidrs)
    client_ip = resolve_client_ip(
        peer_ip,
        request.headers.get("cf-connecting-ip", ""),
        request.headers.get("x-forwarded-for", ""),
        settings.trusted_proxy_cidrs,
    )
    # The fallback is only used as an in-memory rate-limit key. It is never
    # persisted with the feedback row.
    identifier = client_ip or peer_ip or "unknown"
    return daily_visitor_hash(identifier, db.get_session_secret()), trusted_proxy


@router.post("", response_model=FeedbackSubmitOut, status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: FeedbackIn, request: Request):
    if not _request_is_same_origin(request):
        raise HTTPException(status_code=403, detail="feedback_origin_rejected")

    rate_key, trusted_proxy = _feedback_key(request)
    if (
        trusted_proxy
        and request.headers.get("x-portfolio-verified-bot", "").lower() == "true"
    ):
        raise HTTPException(status_code=403, detail="feedback_bot_rejected")

    # Quietly acknowledge filled honeypots without storing or rate-limiting them.
    if payload.website:
        return FeedbackSubmitOut(ok=True)

    if not feedback_rate_limiter.allow(
        rate_key,
        limit=FEEDBACK_RATE_LIMIT,
        window_seconds=FEEDBACK_RATE_WINDOW_SECONDS,
    ):
        raise HTTPException(status_code=429, detail="feedback_rate_limited")

    comment = _clean_comment(payload.comment)
    if len(comment) > _MAX_COMMENT_LENGTH:
        raise HTTPException(status_code=422, detail="comment_too_long")

    try:
        feedback_storage.record_feedback(payload.rating, comment, payload.source)
    except sqlite3.Error:
        log.exception("feedback storage failed")
        raise HTTPException(status_code=503, detail="feedback_unavailable")

    return FeedbackSubmitOut(ok=True)


@router.get("", response_model=FeedbackSummaryOut, dependencies=[Depends(require_admin)])
def get_feedback(response: Response):
    response.headers["Cache-Control"] = "private, no-store"
    return feedback_storage.feedback_summary()
