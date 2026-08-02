"""FastAPI application entrypoint.

The backend serves the portfolio and records analytics only after a short-lived
signed seed and a server-validated Cloudflare Turnstile confirmation.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import analytics_security, db, feedback_storage
from .analytics_security import (
    InvalidAnalyticsToken,
    TURNSTILE_ACTION,
    confirm_rate_limiter,
    create_analytics_seed,
    create_human_token,
    verify_analytics_seed,
    verify_human_token,
)
from .analytics_storage import (
    analytics,
    consume_nonce,
    increment_counter,
    init_analytics_schema,
    record_confirmed_visit,
)
from .config import settings, validate_production_settings
from .db import init_db, load_content
from .privacy import (
    _is_trusted_proxy,
    daily_visitor_hash,
    referrer_hostname,
    resolve_client_ip,
)
from .restore_upload import RestoreUploadTooLarge, stage_restore_upload
from .routers import content, feedback, now, open_source, projects, stats, upload, uptime
from .security import require_admin, router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("portfolio")

SITE_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_ROOT = Path(__file__).resolve().parent / "static"
PUBLIC_FILES = {"index.html", "impressum.html", "datenschutz.html", "og.png"}
_ANALYTICS_PAGES = {"/", "/index.html", "/impressum.html", "/datenschutz.html"}
_BROWSER_SIGNATURES = (
    "chrome/",
    "crios/",
    "edg/",
    "firefox/",
    "fxios/",
    "opr/",
    "safari/",
)
_AUTOMATION_PATTERN = re.compile(
    r"(?:bot|crawler|spider|slurp|headless|lighthouse|pagespeed|"
    r"curl|wget|python-requests|httpx|aiohttp|scrapy|okhttp|"
    r"go-http-client|libwww|zgrab|masscan|nikto|sqlmap)",
    re.IGNORECASE,
)
_ALLOWED_FETCH_SITES = {"none", "same-origin", "same-site"}
_ANALYTICS_COOKIE_PATH = "/api/analytics/confirm"


class AnalyticsConfirmIn(BaseModel):
    path: str = Field(min_length=1, max_length=255)
    turnstile_token: str = Field(default="", max_length=4096)


def _valid_analytics_path(
    path: str, project_slugs: set[str] | None = None
) -> bool:
    if path in _ANALYTICS_PAGES:
        return True
    if path.startswith("/p/") and path.count("/") == 2:
        slug = path.removeprefix("/p/")
        return bool(slug and slug in (project_slugs or set()))
    return False


def _is_analytics_page_response(
    *,
    method: str,
    path: str,
    status_code: int,
    accept: str,
    project_slugs: set[str] | None = None,
) -> bool:
    return bool(
        method.upper() == "GET"
        and 200 <= status_code < 400
        and _valid_analytics_path(path, project_slugs)
        and "text/html" in accept.lower()
    )


def _page_rejection_reason(
    *,
    user_agent: str,
    sec_fetch_dest: str,
    sec_fetch_mode: str,
    sec_fetch_site: str,
    sec_fetch_user: str,
    purpose: str,
    do_not_track: str,
    global_privacy_control: str,
    verified_bot: bool,
) -> str:
    if verified_bot:
        return "known_bot"
    if do_not_track == "1" or global_privacy_control == "1":
        return "privacy_opt_out"
    if purpose.lower() in {"prefetch", "prerender"}:
        return "prefetch"

    normalized_agent = user_agent.strip().lower()
    if (
        not normalized_agent.startswith("mozilla/5.0")
        or _AUTOMATION_PATTERN.search(normalized_agent)
        or not any(token in normalized_agent for token in _BROWSER_SIGNATURES)
    ):
        return "automated_client"

    fetch_headers = (
        sec_fetch_dest,
        sec_fetch_mode,
        sec_fetch_site,
        sec_fetch_user,
    )
    if any(not value for value in fetch_headers):
        return "missing_fetch_metadata"
    if (
        sec_fetch_dest.lower() != "document"
        or sec_fetch_mode.lower() != "navigate"
        or sec_fetch_site.lower() not in _ALLOWED_FETCH_SITES
        or sec_fetch_user != "?1"
    ):
        return "invalid_navigation"
    return ""


def _is_likely_human_page_view(
    *,
    method: str,
    path: str,
    status_code: int,
    accept: str,
    user_agent: str,
    sec_fetch_dest: str = "",
    sec_fetch_mode: str = "",
    sec_fetch_site: str = "",
    sec_fetch_user: str = "",
    purpose: str = "",
    do_not_track: str = "",
    global_privacy_control: str = "",
    verified_bot: bool = False,
    project_slugs: set[str] | None = None,
) -> bool:
    """Return whether a response may receive a seed, never whether it is human."""
    if not _is_analytics_page_response(
        method=method,
        path=path,
        status_code=status_code,
        accept=accept,
        project_slugs=project_slugs,
    ):
        return False
    return not _page_rejection_reason(
        user_agent=user_agent,
        sec_fetch_dest=sec_fetch_dest,
        sec_fetch_mode=sec_fetch_mode,
        sec_fetch_site=sec_fetch_site,
        sec_fetch_user=sec_fetch_user,
        purpose=purpose,
        do_not_track=do_not_track,
        global_privacy_control=global_privacy_control,
        verified_bot=verified_bot,
    )


def _project_slugs() -> set[str]:
    return {
        item.get("slug", "")
        for item in load_content().get("projects", [])
        if item.get("slug")
    }


def _request_client_ip(request: Request) -> tuple[str, str, bool]:
    peer_ip = request.client.host if request.client else ""
    trusted_proxy = _is_trusted_proxy(peer_ip, settings.trusted_proxy_cidrs)
    client_ip = resolve_client_ip(
        peer_ip,
        request.headers.get("cf-connecting-ip", ""),
        request.headers.get("x-forwarded-for", ""),
        settings.trusted_proxy_cidrs,
    )
    return peer_ip, client_ip, trusted_proxy


def _verified_bot(request: Request, trusted_proxy: bool) -> bool:
    return bool(
        trusted_proxy
        and request.headers.get("x-portfolio-verified-bot", "").lower() == "true"
    )


def _analytics_origin_is_valid(request: Request) -> bool:
    hostname = settings.analytics_hostname.lower().rstrip(".")
    if not hostname:
        return False
    expected_scheme = "https" if settings.is_production else request.url.scheme
    expected_origin = f"{expected_scheme}://{hostname}"
    return request.headers.get("origin", "").lower().rstrip("/") == expected_origin


def _confirm_fetch_metadata_is_valid(request: Request) -> bool:
    return bool(
        request.headers.get("sec-fetch-site", "").lower() == "same-origin"
        and request.headers.get("sec-fetch-mode", "").lower() == "cors"
        and request.headers.get("sec-fetch-dest", "").lower() == "empty"
    )


def _inject_script(path: Path, script_path: str) -> HTMLResponse:
    html = path.read_text(encoding="utf-8")
    tag = f'<script src="{script_path}" defer></script>'
    if tag not in html:
        html = html.replace("</body>", f"{tag}\n</body>", 1)
    return HTMLResponse(html)


def _public_html(name: str) -> HTMLResponse:
    return _inject_script(SITE_ROOT / name, "/api/analytics/client.js")


def _silence_connection_reset(loop, context):
    exc = context.get("exception")
    msg = context.get("message", "")
    if exc and isinstance(exc, (ConnectionResetError, ConnectionAbortedError)):
        return
    if "call_connection_lost" in msg or "Connection lost" in msg:
        return
    loop.default_exception_handler(context)


def _security_headers() -> dict[str, str]:
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "media-src 'self'; "
        "connect-src 'self' https://challenges.cloudflare.com; "
        "frame-src https://challenges.cloudflare.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )
    if settings.is_production:
        csp += "; upgrade-insecure-requests"
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Frame-Options": "DENY",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
        "Content-Security-Policy": csp,
    }
    if settings.is_production:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers


def create_app() -> FastAPI:
    validate_production_settings()
    init_db()
    init_analytics_schema()
    feedback_storage.init_feedback_schema()
    log.info("database ready at data/portfolio.db")
    if settings.analytics_strict and not settings.strict_analytics_ready:
        log.warning(
            "strict analytics is disabled until Turnstile site/secret keys are configured"
        )

    docs_url = "/api/docs" if settings.expose_docs else None
    openapi_url = "/api/openapi.json" if settings.expose_docs else None
    app = FastAPI(
        title="Portfolio API",
        version="1.1.0",
        docs_url=docs_url,
        redoc_url=None,
        openapi_url=openapi_url,
    )

    @app.on_event("startup")
    async def _silence_reset():
        asyncio.get_event_loop().set_exception_handler(_silence_connection_reset)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        for key, value in _security_headers().items():
            response.headers.setdefault(key, value)
        return response

    @app.middleware("http")
    async def issue_analytics_seed(request: Request, call_next):
        response = await call_next(request)
        try:
            path = request.url.path
            slugs = _project_slugs() if path.startswith("/p/") else set()
            if not _is_analytics_page_response(
                method=request.method,
                path=path,
                status_code=response.status_code,
                accept=request.headers.get("accept", ""),
                project_slugs=slugs,
            ):
                return response

            increment_counter("page_request")
            _, client_ip, trusted_proxy = _request_client_ip(request)
            rejection = _page_rejection_reason(
                user_agent=request.headers.get("user-agent", ""),
                sec_fetch_dest=request.headers.get("sec-fetch-dest", ""),
                sec_fetch_mode=request.headers.get("sec-fetch-mode", ""),
                sec_fetch_site=request.headers.get("sec-fetch-site", ""),
                sec_fetch_user=request.headers.get("sec-fetch-user", ""),
                purpose=(
                    request.headers.get("sec-purpose", "")
                    or request.headers.get("purpose", "")
                ),
                do_not_track=request.headers.get("dnt", ""),
                global_privacy_control=request.headers.get("sec-gpc", ""),
                verified_bot=_verified_bot(request, trusted_proxy),
            )
            if rejection:
                increment_counter(rejection)
                return response
            if not settings.strict_analytics_ready:
                increment_counter("analytics_unconfigured")
                return response

            visitor_hash = daily_visitor_hash(
                client_ip, db.get_session_secret()
            )
            if not visitor_hash:
                increment_counter("invalid_seed")
                return response
            seed = create_analytics_seed(
                path=path,
                visitor_hash=visitor_hash,
                referrer=referrer_hostname(request.headers.get("referer", "")),
                secret=db.get_session_secret(),
                ttl_seconds=settings.analytics_seed_ttl_seconds,
            )
            response.set_cookie(
                settings.analytics_seed_cookie,
                seed,
                max_age=settings.analytics_seed_ttl_seconds,
                path=_ANALYTICS_COOKIE_PATH,
                secure=settings.secure_cookies,
                httponly=True,
                samesite="lax",
            )
            response.headers["Cache-Control"] = "private, no-store"
            increment_counter("seed_issued")
        except Exception:
            log.exception("analytics seed generation failed")
        return response

    @app.get("/api/health")
    def health():
        return {"ok": True, "service": "portfolio-api"}

    @app.head("/api/health")
    def health_head():
        return Response(status_code=200)

    @app.get("/api/analytics", dependencies=[Depends(require_admin)])
    def get_analytics(days: int = 30):
        return analytics(days)

    @app.get("/api/analytics/client.js", include_in_schema=False)
    def analytics_client_script():
        return FileResponse(
            STATIC_ROOT / "analytics.js",
            media_type="application/javascript",
            headers={"Cache-Control": "public, max-age=3600"},
        )

    @app.get("/api/admin/analytics-ui.js", include_in_schema=False)
    def analytics_admin_script():
        return FileResponse(
            STATIC_ROOT / "admin-analytics.js",
            media_type="application/javascript",
            headers={"Cache-Control": "private, max-age=300"},
        )

    @app.post("/api/analytics/confirm")
    async def confirm_analytics(payload: AnalyticsConfirmIn, request: Request):
        if not settings.strict_analytics_ready:
            raise HTTPException(status_code=503, detail="analytics_unavailable")

        slugs = _project_slugs() if payload.path.startswith("/p/") else set()
        if not _valid_analytics_path(payload.path, slugs):
            increment_counter("invalid_seed")
            raise HTTPException(status_code=400, detail="invalid_path")
        if not _analytics_origin_is_valid(request):
            increment_counter("invalid_origin")
            raise HTTPException(status_code=403, detail="invalid_origin")
        if not _confirm_fetch_metadata_is_valid(request):
            increment_counter("missing_fetch_metadata")
            raise HTTPException(status_code=403, detail="invalid_fetch_metadata")

        _, client_ip, trusted_proxy = _request_client_ip(request)
        if _verified_bot(request, trusted_proxy):
            increment_counter("known_bot")
            raise HTTPException(status_code=403, detail="known_bot")
        visitor_hash = daily_visitor_hash(client_ip, db.get_session_secret())
        seed_token = request.cookies.get(settings.analytics_seed_cookie, "")
        try:
            seed = verify_analytics_seed(
                seed_token,
                path=payload.path,
                visitor_hash=visitor_hash,
                secret=db.get_session_secret(),
                ttl_seconds=settings.analytics_seed_ttl_seconds,
            )
        except InvalidAnalyticsToken as exc:
            increment_counter("invalid_seed")
            raise HTTPException(status_code=403, detail="invalid_seed") from exc

        human_cookie = request.cookies.get(settings.analytics_human_cookie, "")
        has_human_cookie = verify_human_token(
            human_cookie,
            visitor_hash=visitor_hash,
            secret=db.get_session_secret(),
        )
        if not has_human_cookie and not payload.turnstile_token:
            return JSONResponse(
                {
                    "detail": "turnstile_required",
                    "site_key": settings.turnstile_site_key,
                    "action": TURNSTILE_ACTION,
                },
                status_code=428,
            )

        if not confirm_rate_limiter.allow(
            visitor_hash,
            limit=settings.analytics_confirm_rate_limit,
            window_seconds=settings.analytics_confirm_rate_window_seconds,
        ):
            increment_counter("rate_limited")
            raise HTTPException(status_code=429, detail="rate_limited")

        if not has_human_cookie:
            turnstile = await analytics_security.verify_turnstile_token(
                token=payload.turnstile_token,
                remote_ip=client_ip,
                secret_key=settings.turnstile_secret_key,
                expected_hostname=settings.analytics_hostname,
                expected_action=TURNSTILE_ACTION,
            )
            if turnstile.unavailable:
                increment_counter("turnstile_unavailable")
                raise HTTPException(
                    status_code=503, detail="turnstile_unavailable"
                )
            if not turnstile.valid:
                increment_counter("turnstile_failed")
                raise HTTPException(status_code=403, detail="turnstile_failed")

        if not consume_nonce(seed["nonce"], seed["exp"]):
            increment_counter("replayed_seed")
            raise HTTPException(status_code=409, detail="seed_replayed")

        counted = record_confirmed_visit(
            payload.path,
            str(seed.get("referrer", "")),
            visitor_hash,
            verification_method="turnstile",
            confidence=100,
        )
        increment_counter("confirmation_received")
        response = JSONResponse({"ok": True, "counted": counted})
        response.delete_cookie(
            settings.analytics_seed_cookie,
            path=_ANALYTICS_COOKIE_PATH,
        )
        if not has_human_cookie:
            human_token, expires_at = create_human_token(
                visitor_hash=visitor_hash,
                secret=db.get_session_secret(),
            )
            response.set_cookie(
                settings.analytics_human_cookie,
                human_token,
                expires=datetime.fromtimestamp(expires_at, timezone.utc),
                path=_ANALYTICS_COOKIE_PATH,
                secure=settings.secure_cookies,
                httponly=True,
                samesite="lax",
            )
        return response

    @app.get("/api/project/{slug}")
    def get_project(slug: str, lang: str = "de"):
        data = load_content()
        for project in data.get("projects", []):
            if project.get("slug") == slug:
                result = dict(project)
                if lang == "en":
                    translations = data.get("translations", {})
                    english = translations.get("en", {}) if isinstance(translations, dict) else {}
                    english = english if isinstance(english, dict) else {}
                    translated = next(
                        (
                            item
                            for item in english.get("projects", [])
                            if item.get("slug") == slug
                        ),
                        None,
                    )
                    if isinstance(translated, dict):
                        for field in ("title", "desc", "stack", "content"):
                            if isinstance(translated.get(field), str):
                                result[field] = translated[field]
                        if isinstance(translated.get("badges"), list):
                            result["badges"] = [
                                {
                                    **badge,
                                    **(
                                        {"label": translated["badges"][index]["label"]}
                                        if index < len(translated["badges"])
                                        and isinstance(translated["badges"][index], dict)
                                        and isinstance(translated["badges"][index].get("label"), str)
                                        else {}
                                    ),
                                }
                                for index, badge in enumerate(result.get("badges", []))
                            ]
                        result["_localized"] = "en"
                return result
        return JSONResponse({"detail": "project not found"}, status_code=404)

    @app.get("/api/backup", dependencies=[Depends(require_admin)])
    def download_backup():
        if not db.DB_PATH.exists():
            return JSONResponse({"detail": "no database yet"}, status_code=404)
        data = db.DB_PATH.read_bytes()
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        return Response(
            content=data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="portfolio-{ts}.db"'},
        )

    @app.post("/api/restore", dependencies=[Depends(require_admin)])
    async def restore_backup(file: UploadFile = File(...)):
        db.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        temp_path: Path | None = None
        try:
            try:
                temp_path, written = await stage_restore_upload(
                    file, db.DB_PATH.parent, settings.restore_max_bytes
                )
            except RestoreUploadTooLarge as exc:
                raise HTTPException(
                    status_code=413,
                    detail="backup exceeds the restore size limit",
                ) from exc
            if written == 0:
                raise HTTPException(status_code=400, detail="backup is empty")

            restored_bytes, backup_path = db.restore_database(temp_path)
            temp_path = None
            init_analytics_schema()
            feedback_storage.init_feedback_schema()
            log.info(
                "database restore completed; pre-restore backup saved as %s",
                backup_path.name,
            )
            return {"ok": True, "bytes": restored_bytes}
        except db.RestoreValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            await file.close()
            if temp_path is not None:
                try:
                    temp_path.unlink()
                except FileNotFoundError:
                    pass

    app.include_router(auth_router)
    app.include_router(content.router)
    app.include_router(feedback.router)
    app.include_router(open_source.router)
    app.include_router(projects.router)
    app.include_router(now.router)
    app.include_router(stats.router)
    app.include_router(uptime.router)
    app.include_router(upload.router)

    @app.get("/admin")
    @app.get("/admin/")
    def admin_page():
        admin_html = SITE_ROOT / "admin" / "admin.html"
        if admin_html.is_file():
            return _inject_script(
                admin_html, "/api/admin/analytics-ui.js"
            )
        return _public_html("index.html")

    @app.get("/p/{slug}")
    def project_page(slug: str):
        deep = SITE_ROOT / "p" / "page.html"
        if deep.is_file():
            if slug in _project_slugs():
                return _inject_script(deep, "/api/analytics/client.js")
            return FileResponse(deep)
        return _public_html("index.html")

    for sub in ("vids", "new_image", "uploads"):
        directory = SITE_ROOT / sub
        directory.mkdir(parents=True, exist_ok=True)
        app.mount(
            f"/{sub}", StaticFiles(directory=directory), name=sub
        )

    @app.get("/{path:path}")
    def index(path: str):
        if path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        if path == "":
            return _public_html("index.html")
        if path in {"index.html", "impressum.html", "datenschutz.html"}:
            candidate = SITE_ROOT / path
            if candidate.is_file():
                return _public_html(path)
        if path in {"locale.js", "locale-content.js", "locale-controller.js", "locale-fixes.js", "locale-runtime-fixes.js", "locale-project.js", "locale-project-fixes.js", "legal-locale.js"}:
            candidate = SITE_ROOT / path
            if candidate.is_file():
                return FileResponse(candidate, media_type="application/javascript")
        if path == "og.png":
            return FileResponse(SITE_ROOT / path)
        return FileResponse(SITE_ROOT / "index.html")

    return app


app = create_app()
