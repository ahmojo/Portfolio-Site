"""Image upload router (admin-only).

Stores uploaded images in <repo-root>/uploads/, served publicly at /uploads/...
Used by the admin panel for certificate images and project media, so the user
never has to manually drop files into new_image/.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel

from ..config import settings
from ..security import require_admin

router = APIRouter(prefix="/api/upload", tags=["upload"])

# repo root: upload.py lives in <repo>/backend/app/routers/upload.py,
# so 4 levels up gets us out of backend/ entirely (matches main.py's SITE_ROOT).
REPO_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_DIR = REPO_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
# sniff first bytes — cheap validation that the file is actually an image
MAGIC = {
    b"\x89PNG": ".png",
    b"\xff\xd8\xff": ".jpg",
    b"GIF8": ".gif",
    b"RIFF": ".webp",   # RIFF....WEBP
}


def _slugify(name: str) -> str:
    """Make a filename filesystem-safe and ascii."""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^\w.\-]+", "-", name).strip("-_.")
    return name or "file"


def _detect_ext(data: bytes, fallback: str) -> str:
    for magic, ext in MAGIC.items():
        if data.startswith(magic):
            return ext
    return fallback.lower() if fallback.lower() in ALLOWED_EXT else ".png"


class UploadOut(BaseModel):
    ok: bool = True
    url: str
    filename: str
    bytes: int


@router.post("", response_model=UploadOut, dependencies=[Depends(require_admin)])
async def upload_image(file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "empty file")
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, f"file too large (max {MAX_BYTES // 1024 // 1024} MB)")

    ext = _detect_ext(raw, Path(file.filename or "").suffix)
    base = _slugify(Path(file.filename or "upload").stem)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    # de-duplicate + avoid collisions with a timestamp
    safe_name = f"{base}-{ts}{ext}"

    dest = UPLOAD_DIR / safe_name
    dest.write_bytes(raw)

    return UploadOut(url=f"/uploads/{safe_name}", filename=safe_name, bytes=len(raw))


class UploadList(BaseModel):
    files: list[dict]


@router.get("", response_model=UploadList, dependencies=[Depends(require_admin)])
def list_uploads():
    files = []
    for p in sorted(UPLOAD_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if p.is_file():
            files.append({
                "url": f"/uploads/{p.name}",
                "filename": p.name,
                "bytes": p.stat().st_size,
            })
    return UploadList(files=files)


@router.delete("", dependencies=[Depends(require_admin)])
def delete_upload(filename: str):
    """Delete an uploaded file by name. Validates the path stays inside uploads/."""
    target = (UPLOAD_DIR / filename).resolve()
    if not str(target).startswith(str(UPLOAD_DIR.resolve())):
        raise HTTPException(400, "invalid filename")
    if not target.exists():
        raise HTTPException(404, "not found")
    target.unlink()
    return {"ok": True}
