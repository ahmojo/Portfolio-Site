"""Bounded, disk-backed staging for database restore uploads."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Protocol


class AsyncUpload(Protocol):
    async def read(self, size: int = -1) -> bytes: ...


class RestoreUploadTooLarge(ValueError):
    """Raised when a restore upload exceeds its configured byte limit."""


async def stage_restore_upload(
    upload: AsyncUpload, directory: Path, max_bytes: int
) -> tuple[Path, int]:
    """Stream an upload into the DB directory without buffering it in memory."""
    directory.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    written = 0
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".portfolio-restore-",
            suffix=".db",
            dir=directory,
            delete=False,
        ) as temp:
            temp_path = Path(temp.name)
            while chunk := await upload.read(64 * 1024):
                written += len(chunk)
                if written > max_bytes:
                    raise RestoreUploadTooLarge
                temp.write(chunk)
            temp.flush()
        return temp_path, written
    except Exception:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
        raise
