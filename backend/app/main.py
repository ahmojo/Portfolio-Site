"""FastAPI application entrypoint.

The backend serves both the public portfolio pages and the `/api/*` routes.
Only intentional public files are served; backend internals and runtime state
must never be exposed through the static fallback.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import Depends, FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .config import settings, validate_production_settings
from .db import DB_PATH, analytics, init_db, load_content, record_visit
from .routers import content, now, projects, stats, upload, uptime
from .security import require_admin, router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("portfolio")

SITE_ROOT = Path(__file__).resolve().parent.parent.parent
PUBLIC_FILES = {"index.html", "impressum.html", "datenschutz.html", "og.png"}


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
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "media-src 'self'; "
        "connect-src 'self'; "
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
    log.info("database ready at data/portfolio.db")

    docs_url = "/api/docs" if settings.expose_docs else None
    openapi_url = "/api/openapi.json" if settings.expose_docs else None
    app = FastAPI(
        title="Portfolio API",
        version="1.0.0",
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
    async def track_visits(request: Request, call_next):
        response = await call_next(request)
        try:
            path = request.url.path
            if (
                path.startswith("/api")
                or path.startswith("/vids")
                or path.startswith("/new_image")
                or path.startswith("/admin")
                or "." in path.rsplit("/", 1)[-1]
            ):
                return response
            ip = (
                request.headers.get("cf-connecting-ip", "").split(",")[0].strip()
                or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                or (request.client.host if request.client else "")
            )
            record_visit(
                path,
                request.headers.get("referer", ""),
                request.headers.get("user-agent", ""),
                ip,
            )
        except Exception:
            pass
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

    @app.get("/api/project/{slug}")
    def get_project(slug: str):
        data = load_content()
        for p in data.get("projects", []):
            if p.get("slug") == slug:
                return p
        return JSONResponse({"detail": "project not found"}, status_code=404)

    @app.get("/api/backup", dependencies=[Depends(require_admin)])
    def download_backup():
        if not DB_PATH.exists():
            return JSONResponse({"detail": "no database yet"}, status_code=404)
        data = DB_PATH.read_bytes()
        ts = __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S")
        return Response(
            content=data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="portfolio-{ts}.db"'},
        )

    @app.post("/api/restore", dependencies=[Depends(require_admin)])
    async def restore_backup(file: UploadFile = File(...)):
        data = await file.read()
        if not data.startswith(b"SQLite format 3"):
            return JSONResponse({"detail": "not a valid SQLite file"}, status_code=400)
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        DB_PATH.write_bytes(data)
        return {"ok": True, "bytes": len(data)}

    app.include_router(auth_router)
    app.include_router(content.router)
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
            return FileResponse(admin_html)
        return FileResponse(SITE_ROOT / "index.html")

    @app.get("/p/{slug}")
    def project_page(slug: str):
        deep = SITE_ROOT / "p" / "page.html"
        if deep.is_file():
            return FileResponse(deep)
        return FileResponse(SITE_ROOT / "index.html")

    for sub in ("vids", "new_image", "uploads"):
        d = SITE_ROOT / sub
        d.mkdir(parents=True, exist_ok=True)
        app.mount(f"/{sub}", StaticFiles(directory=d), name=sub)

    @app.get("/{path:path}")
    def index(path: str):
        if path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        if path in PUBLIC_FILES:
            candidate = SITE_ROOT / path
            if candidate.is_file():
                return FileResponse(candidate)
        return FileResponse(SITE_ROOT / "index.html")

    return app


app = create_app()
