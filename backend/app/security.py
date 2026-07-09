"""Admin authentication with HMAC-signed session cookies."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

from .config import settings
from .db import get_session_secret

router = APIRouter(prefix="/api/auth", tags=["auth"])
log = logging.getLogger("portfolio.auth")
_FAILED_LOGINS: dict[str, list[float]] = {}


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _ub64(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _sign(payload_b64: str, exp: int) -> str:
    secret = get_session_secret().encode()
    msg = f"{exp}.{payload_b64}".encode()
    return _b64(hmac.new(secret, msg, hashlib.sha256).digest())


def create_token(ttl_hours: Optional[int] = None) -> tuple[str, int]:
    ttl = ttl_hours if ttl_hours is not None else settings.session_ttl_hours
    exp = int(time.time()) + ttl * 3600
    payload = _b64(json.dumps({"exp": exp, "rnd": secrets.token_hex(8)}).encode())
    sig = _sign(payload, exp)
    return f"{exp}.{payload}.{sig}", exp


def verify_token(token: str) -> bool:
    if not token or token.count(".") != 2:
        return False
    exp_str, payload, sig = token.split(".")
    try:
        exp = int(exp_str)
    except ValueError:
        return False
    if exp < time.time():
        return False
    expected = _sign(payload, exp)
    return hmac.compare_digest(sig, expected)


def _cookie_attrs() -> dict:
    return dict(
        key=settings.session_cookie,
        httponly=True,
        samesite="lax",
        secure=settings.secure_cookies,
        path="/",
    )


def set_session_cookie(response: Response) -> None:
    token, exp = create_token()
    response.set_cookie(value=token, max_age=int(exp - time.time()), **_cookie_attrs())


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(**_cookie_attrs())


def get_token(request: Request) -> Optional[str]:
    return request.cookies.get(settings.session_cookie)


def is_authenticated(request: Request) -> bool:
    token = get_token(request)
    return bool(token and verify_token(token))


def require_admin(request: Request):
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": 'Cookie realm="admin"'},
        )


class LoginIn(BaseModel):
    password: str


class LoginOut(BaseModel):
    ok: bool
    authenticated: bool


def _client_ip(request: Request) -> str:
    return (
        request.headers.get("cf-connecting-ip", "").split(",")[0].strip()
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "")
        or "unknown"
    )


def _recent_failures(ip: str, now: float) -> list[float]:
    window = settings.login_rate_limit_window_seconds
    failures = [ts for ts in _FAILED_LOGINS.get(ip, []) if now - ts < window]
    if failures:
        _FAILED_LOGINS[ip] = failures
    else:
        _FAILED_LOGINS.pop(ip, None)
    return failures


def _rate_limited(ip: str, now: float) -> bool:
    return len(_recent_failures(ip, now)) >= settings.login_rate_limit_attempts


def _record_failed_login(ip: str, now: float) -> None:
    failures = _recent_failures(ip, now)
    failures.append(now)
    _FAILED_LOGINS[ip] = failures


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, request: Request, response: Response):
    ip = _client_ip(request)
    now = time.time()
    if _rate_limited(ip, now):
        log.warning("admin login rate limited from %s", ip)
        raise HTTPException(status_code=429, detail="Too many login attempts.")

    ok = secrets.compare_digest(payload.password, settings.admin_password)
    if not ok:
        _record_failed_login(ip, now)
        log.warning("admin login failed from %s", ip)
        time.sleep(0.15)
        return LoginOut(ok=False, authenticated=False)

    _FAILED_LOGINS.pop(ip, None)
    set_session_cookie(response)
    return LoginOut(ok=True, authenticated=True)


@router.post("/logout", response_model=LoginOut)
def logout(response: Response):
    clear_session_cookie(response)
    return LoginOut(ok=True, authenticated=False)


@router.get("/me", response_model=LoginOut)
def me(request: Request):
    return LoginOut(ok=True, authenticated=is_authenticated(request))
