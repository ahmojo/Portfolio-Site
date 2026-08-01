"""Signed analytics tokens, Turnstile verification, and confirm rate limiting."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

TURNSTILE_ACTION = "portfolio_analytics"
TURNSTILE_SITEVERIFY_URL = (
    "https://challenges.cloudflare.com/turnstile/v0/siteverify"
)


class InvalidAnalyticsToken(ValueError):
    """Raised when a signed analytics token is invalid or expired."""


@dataclass(frozen=True)
class TurnstileResult:
    valid: bool
    unavailable: bool = False
    error_codes: tuple[str, ...] = ()


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except (ValueError, TypeError) as exc:
        raise InvalidAnalyticsToken("invalid token encoding") from exc


def _sign(payload: dict, secret: str, purpose: str) -> str:
    encoded = _b64encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    )
    signature = hmac.new(
        secret.encode(), f"{purpose}\0{encoded}".encode(), hashlib.sha256
    ).digest()
    return f"{encoded}.{_b64encode(signature)}"


def _verify(token: str, secret: str, purpose: str) -> dict:
    if not token or not secret:
        raise InvalidAnalyticsToken("missing token")
    try:
        encoded, supplied_signature = token.split(".", 1)
    except ValueError as exc:
        raise InvalidAnalyticsToken("invalid token format") from exc
    expected_signature = hmac.new(
        secret.encode(), f"{purpose}\0{encoded}".encode(), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(
        expected_signature, _b64decode(supplied_signature)
    ):
        raise InvalidAnalyticsToken("invalid token signature")
    try:
        payload = json.loads(_b64decode(encoded))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidAnalyticsToken("invalid token payload") from exc
    if not isinstance(payload, dict):
        raise InvalidAnalyticsToken("invalid token payload")
    return payload


def create_analytics_seed(
    *,
    path: str,
    visitor_hash: str,
    referrer: str,
    secret: str,
    ttl_seconds: int,
    now: int | None = None,
) -> str:
    issued_at = int(time.time() if now is None else now)
    return _sign(
        {
            "v": 1,
            "kind": "analytics_seed",
            "path": path,
            "visitor": visitor_hash,
            "referrer": referrer,
            "nonce": secrets.token_urlsafe(24),
            "iat": issued_at,
            "exp": issued_at + ttl_seconds,
        },
        secret,
        "analytics-seed",
    )


def verify_analytics_seed(
    token: str,
    *,
    path: str,
    visitor_hash: str,
    secret: str,
    ttl_seconds: int,
    now: int | None = None,
) -> dict:
    payload = _verify(token, secret, "analytics-seed")
    current_time = int(time.time() if now is None else now)
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    if (
        payload.get("v") != 1
        or payload.get("kind") != "analytics_seed"
        or payload.get("path") != path
        or payload.get("visitor") != visitor_hash
        or not isinstance(issued_at, int)
        or not isinstance(expires_at, int)
        or expires_at <= current_time
        or issued_at > current_time + 30
        or expires_at - issued_at != ttl_seconds
        or not isinstance(payload.get("nonce"), str)
        or len(payload["nonce"]) < 20
    ):
        raise InvalidAnalyticsToken("seed claims do not match")
    return payload


def create_human_token(
    *,
    visitor_hash: str,
    secret: str,
    now: datetime | None = None,
) -> tuple[str, int]:
    current = now or datetime.now(timezone.utc)
    end_of_day = datetime.combine(
        current.date() + timedelta(days=1),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    expires_at = int(end_of_day.timestamp())
    payload = {
        "v": 1,
        "kind": "human_verified",
        "visitor": visitor_hash,
        "method": "turnstile",
        "iat": int(current.timestamp()),
        "exp": expires_at,
    }
    return _sign(payload, secret, "analytics-human"), expires_at


def verify_human_token(
    token: str,
    *,
    visitor_hash: str,
    secret: str,
    now: int | None = None,
) -> bool:
    try:
        payload = _verify(token, secret, "analytics-human")
    except InvalidAnalyticsToken:
        return False
    current_time = int(time.time() if now is None else now)
    return bool(
        payload.get("v") == 1
        and payload.get("kind") == "human_verified"
        and payload.get("visitor") == visitor_hash
        and payload.get("method") == "turnstile"
        and isinstance(payload.get("iat"), int)
        and isinstance(payload.get("exp"), int)
        and payload["iat"] <= current_time + 30
        and payload["exp"] > current_time
    )


async def verify_turnstile_token(
    *,
    token: str,
    remote_ip: str,
    secret_key: str,
    expected_hostname: str,
    expected_action: str = TURNSTILE_ACTION,
) -> TurnstileResult:
    """Validate a single-use Turnstile token with Cloudflare Siteverify."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                TURNSTILE_SITEVERIFY_URL,
                data={
                    "secret": secret_key,
                    "response": token,
                    "remoteip": remote_ip,
                },
            )
            response.raise_for_status()
            result = response.json()
    except (httpx.HTTPError, json.JSONDecodeError, ValueError):
        return TurnstileResult(valid=False, unavailable=True)

    error_codes = result.get("error-codes") or []
    if not isinstance(error_codes, list):
        error_codes = []
    valid = bool(
        result.get("success") is True
        and str(result.get("hostname", "")).lower().rstrip(".")
        == expected_hostname.lower().rstrip(".")
        and result.get("action") == expected_action
    )
    return TurnstileResult(
        valid=valid,
        error_codes=tuple(str(code) for code in error_codes),
    )


class SlidingWindowRateLimiter:
    """Small in-memory limiter suitable for this single-worker deployment."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> bool:
        current = time.monotonic() if now is None else now
        cutoff = current - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(current)
            return True

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


confirm_rate_limiter = SlidingWindowRateLimiter()
