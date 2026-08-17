"""GitHub client with memory and persistent caches.

Keeps the project list responsive and avoids hammering the GitHub API
(anonymous rate limit is 60 req/h per IP).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import tempfile
import time
from datetime import date
from pathlib import Path
from typing import Any, Optional

import httpx

from .config import settings

log = logging.getLogger("portfolio.github")

_GH_API = "https://api.github.com"
_CCT_REPO = "ahmojo/codex-claude-transfer"
_CCT_METRICS_URL = (
    "https://raw.githubusercontent.com/ahmojo/codex-claude-transfer/"
    "metrics/metrics/traffic.json"
)
_CCT_RELEASE_CACHE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "cct-release-downloads.json"
)
_CCT_RELEASE_CACHE_SCHEMA_VERSION = 1
_USAGE_TTL = 3600
_BINARY_ASSET_RE = re.compile(
    r"^(?:cct|codex-sync)_v[^_]+_(?:linux|darwin|windows)_"
    r"(?:amd64|arm64)\.(?:tar\.gz|zip)$",
    re.IGNORECASE,
)
_SNAPSHOT_FIELDS = (
    "release_downloads",
    "clones_14d",
    "unique_cloners_14d",
    "tracked_total_clones",
)

_cache: dict[str, dict] = {}          # repo -> data
_cache_ts: dict[str, float] = {}      # repo -> fetch timestamp
_usage_cache: dict[str, dict[str, Any]] = {}
_usage_attempt_ts: dict[str, float] = {}
_lock = asyncio.Lock()


def normalize_repo(value: str) -> str:
    """Return a GitHub repository as owner/name, accepting full URLs too."""
    repo = value.strip()
    repo = re.sub(r"^https?://(?:www\.)?github\.com/", "", repo, flags=re.I)
    repo = repo.split("?", 1)[0].split("#", 1)[0].strip("/")
    if repo.lower().endswith(".git"):
        repo = repo[:-4]
    parts = repo.split("/")
    return "/".join(parts[:2]) if len(parts) >= 2 else repo


def _headers() -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "portfolio-backend/1.0",
    }
    if settings.github_token:
        h["Authorization"] = f"Bearer {settings.github_token}"
    return h


def _read_persisted_release_downloads() -> Optional[int]:
    """Read the last known CCT release count, if a valid cache exists."""
    path = Path(_CCT_RELEASE_CACHE_PATH)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as exc:
        log.warning("CCT release-download cache read failed: %s", exc)
        return None

    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        log.warning("CCT release-download cache is invalid: %s", exc)
        return None

    if not isinstance(payload, dict):
        log.warning("CCT release-download cache is invalid: expected an object")
        return None
    schema_version = payload.get("schema_version")
    if schema_version is not None and (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != _CCT_RELEASE_CACHE_SCHEMA_VERSION
    ):
        log.warning("CCT release-download cache has an unsupported schema")
        return None
    repo = payload.get("repo")
    if repo is not None and str(repo).lower() != _CCT_REPO:
        log.warning("CCT release-download cache belongs to an unexpected repo")
        return None

    value = _optional_non_negative_int(payload.get("release_downloads"))
    if value is None:
        log.warning("CCT release-download cache has no valid count")
    return value


def _known_release_downloads() -> Optional[int]:
    """Return the highest valid value known in memory or on disk."""
    in_memory = _optional_non_negative_int(
        _usage_cache.get(_CCT_REPO, {}).get("release_downloads")
    )
    persisted = _read_persisted_release_downloads()
    if in_memory is None:
        return persisted
    if persisted is None:
        return in_memory
    return max(in_memory, persisted)


def _persist_release_downloads(value: Any) -> None:
    """Atomically persist a validated release count without storing secrets."""
    count = _optional_non_negative_int(value)
    if count is None:
        return

    path = Path(_CCT_RELEASE_CACHE_PATH)
    temporary_path: Optional[Path] = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "schema_version": _CCT_RELEASE_CACHE_SCHEMA_VERSION,
                        "repo": _CCT_REPO,
                        "release_downloads": count,
                    },
                    handle,
                    separators=(",", ":"),
                )
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            # fdopen owns the descriptor after it succeeds; this closes it if
            # opening the wrapper itself failed.
            try:
                os.close(fd)
            except OSError:
                pass
            raise

        os.replace(temporary_path, path)

        # On platforms that support it, flush the directory entry as well.
        # Windows does not allow opening a directory this way, so the file
        # fsync + atomic replace above remains the portable fallback.
        if os.name != "nt":
            try:
                directory_fd = os.open(
                    str(path.parent),
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
                )
            except OSError:
                directory_fd = None
            if directory_fd is not None:
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
    except OSError as exc:
        # A cache write failure must never hide a valid live API value.
        log.warning("CCT release-download cache write failed: %s", exc)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


async def fetch_repo(client: httpx.AsyncClient, repo: str) -> Optional[dict]:
    """Fetch a single repo. Returns None on any error (rate limit, 404...)."""
    try:
        r = await client.get(f"{_GH_API}/repos/{repo}", headers=_headers(), timeout=8.0)
        if r.status_code == 404:
            return {"repo": repo, "stars": 0, "exists": False}
        if r.status_code == 403:
            log.warning("GitHub rate limit hit (403). Serving cached/stale data.")
            return None
        r.raise_for_status()
        d = r.json()
        return {
            "repo": repo,
            "url": d.get("html_url", f"https://github.com/{repo}"),
            "stars": d.get("stargazers_count", 0),
            "forks": d.get("forks_count", 0),
            "language": d.get("language"),
            "updated_at": d.get("pushed_at") or d.get("updated_at"),
            "description": d.get("description"),
            "exists": True,
        }
    except Exception as e:
        log.warning("github fetch failed for %s: %s", repo, e)
        return None


async def fetch_release_downloads(
    client: httpx.AsyncClient, repo: str = _CCT_REPO
) -> Optional[int]:
    """Count downloads of published, installable release binaries."""
    total = 0
    page = 1
    try:
        while True:
            response = await client.get(
                f"{_GH_API}/repos/{repo}/releases",
                headers=_headers(),
                params={"per_page": 100, "page": page},
                timeout=8.0,
            )
            response.raise_for_status()
            releases = response.json()
            if not isinstance(releases, list):
                raise ValueError("GitHub releases response is not a list")
            for release in releases:
                if not isinstance(release, dict) or release.get("draft"):
                    continue
                for asset in release.get("assets", []):
                    if not isinstance(asset, dict):
                        continue
                    if _BINARY_ASSET_RE.fullmatch(str(asset.get("name", ""))):
                        count = asset.get("download_count")
                        if (
                            isinstance(count, int)
                            and not isinstance(count, bool)
                            and count >= 0
                        ):
                            total += count
            if len(releases) < 100:
                if repo.lower() == _CCT_REPO:
                    known = _known_release_downloads()
                    if known is not None and total < known:
                        log.warning(
                            "Ignoring lower CCT release-download count (%s < %s)",
                            total,
                            known,
                        )
                        return known
                if repo.lower() == _CCT_REPO:
                    _persist_release_downloads(total)
                return total
            page += 1
    except Exception as exc:
        log.warning("GitHub release fetch failed for %s: %s", repo, exc)
        return _known_release_downloads() if repo.lower() == _CCT_REPO else None


def _optional_non_negative_int(value: Any) -> Optional[int]:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _validated_metric_snapshots(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    snapshots: list[dict[str, Any]] = []
    for day_key, raw_snapshot in sorted(value.items()):
        if not isinstance(day_key, str) or not isinstance(raw_snapshot, dict):
            continue
        try:
            if date.fromisoformat(day_key).isoformat() != day_key:
                continue
        except ValueError:
            continue
        snapshot: dict[str, Any] = {"date": day_key}
        for field in _SNAPSHOT_FIELDS:
            parsed = _optional_non_negative_int(raw_snapshot.get(field))
            if parsed is not None:
                snapshot[field] = parsed
        if len(snapshot) > 1:
            snapshots.append(snapshot)
    return snapshots


def _daily_metric_deltas(
    current: dict[str, Any], snapshots: list[dict[str, Any]]
) -> dict[str, int]:
    deltas: dict[str, int] = {}
    for field in _SNAPSHOT_FIELDS:
        current_value = _optional_non_negative_int(current.get(field))
        values = [
            snapshot[field]
            for snapshot in snapshots
            if _optional_non_negative_int(snapshot.get(field)) is not None
        ]
        if current_value is None or len(values) < 2:
            continue
        deltas[f"{field}_delta_1d"] = current_value - values[-2]
    return deltas


async def fetch_traffic_metrics(client: httpx.AsyncClient) -> Optional[dict]:
    """Fetch and validate the public clone metrics snapshot."""
    try:
        response = await client.get(_CCT_METRICS_URL, timeout=8.0)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("traffic metrics response is not an object")
        if (
            data.get("schema_version") != 1
            or str(data.get("repo", "")).lower() != _CCT_REPO
        ):
            raise ValueError("unsupported traffic metrics document")
        metrics = {
            "release_downloads": _optional_non_negative_int(
                data.get("release_downloads")
            ),
            "clones_14d": _optional_non_negative_int(data.get("clones_14d")),
            "unique_cloners_14d": _optional_non_negative_int(
                data.get("unique_cloners_14d")
            ),
            "tracked_total_clones": _optional_non_negative_int(
                data.get("tracked_total_clones")
            ),
            "tracked_since": (
                data.get("tracked_since")
                if isinstance(data.get("tracked_since"), str)
                else None
            ),
            "metrics_updated_at": (
                data.get("updated_at")
                if isinstance(data.get("updated_at"), str)
                else None
            ),
            "metrics_history": _validated_metric_snapshots(
                data.get("snapshots")
            ),
        }
        return {
            key: value
            for key, value in metrics.items()
            if value is not None and value != []
        }
    except Exception as exc:
        log.warning("GitHub traffic metrics fetch failed for %s: %s", _CCT_REPO, exc)
        return None


async def fetch_cct_usage(client: httpx.AsyncClient) -> dict[str, Any]:
    """Fetch independent CCT usage sources without coupling their failures."""
    release_downloads, traffic = await asyncio.gather(
        fetch_release_downloads(client), fetch_traffic_metrics(client)
    )
    result: dict[str, Any] = {}
    if traffic is not None:
        result.update(traffic)
    if release_downloads is not None:
        traffic_downloads = _optional_non_negative_int(
            result.get("release_downloads")
        )
        result["release_downloads"] = (
            max(release_downloads, traffic_downloads)
            if traffic_downloads is not None
            else release_downloads
        )
    release_downloads = _optional_non_negative_int(
        result.get("release_downloads")
    )
    if release_downloads is not None:
        # Persist only after both sources have resolved so a slower traffic
        # request cannot overwrite a newer count from the releases API.
        _persist_release_downloads(release_downloads)
    history = result.get("metrics_history")
    if isinstance(history, list):
        result.update(_daily_metric_deltas(result, history))
    return result


async def get_projects(projects: list[tuple[str, str]] | None = None) -> list[dict]:
    """Return project data for all configured repos, using a TTL cache."""
    configured = projects or list(settings.projects.items())
    configured = [
        (name, original, normalize_repo(original))
        for name, original in configured
        if normalize_repo(original)
    ]
    ttl = settings.projects_ttl
    now = time.time()

    async with _lock:
        stale = [
            canonical for _, _, canonical in configured
            if now - _cache_ts.get(canonical, 0) > ttl or canonical not in _cache
        ]

    if stale:
        async with httpx.AsyncClient() as client:
            results = await asyncio.gather(*[fetch_repo(client, r) for r in stale])
        async with _lock:
            for repo, data in zip(stale, results):
                if data is None:
                    # keep previous cache if we have one, else placeholder
                    if repo not in _cache:
                        _cache[repo] = {
                            "repo": repo,
                            "url": f"https://github.com/{repo}",
                            "stars": 0,
                            "forks": 0,
                            "language": None,
                            "updated_at": None,
                            "description": None,
                            "exists": False,
                        }
                        _cache_ts[repo] = now
                else:
                    _cache[repo] = data
                    _cache_ts[repo] = now

    includes_cct = any(repo.lower() == _CCT_REPO for _, _, repo in configured)
    async with _lock:
        usage_stale = (
            includes_cct
            and now - _usage_attempt_ts.get(_CCT_REPO, 0) > _USAGE_TTL
        )
    if usage_stale:
        async with httpx.AsyncClient() as client:
            usage = await fetch_cct_usage(client)
        async with _lock:
            _usage_attempt_ts[_CCT_REPO] = now
            if usage:
                previous = _usage_cache.get(_CCT_REPO, {})
                _usage_cache[_CCT_REPO] = {**previous, **usage}

    out = []
    for name, original, repo in configured:
        data = _cache.get(repo, {})
        project = {
            "name": name,
            "repo": original,
            "url": data.get("url", f"https://github.com/{repo}"),
            "stars": data.get("stars", 0),
            "forks": data.get("forks", 0),
            "language": data.get("language"),
            "updated_at": data.get("updated_at"),
            "description": data.get("description"),
            "exists": data.get("exists", True),
            "cached": (now - _cache_ts.get(repo, now)) < ttl * 0.9,
            "fetched_at": _cache_ts.get(repo),
            "release_downloads": None,
            "clones_14d": None,
            "unique_cloners_14d": None,
            "tracked_total_clones": None,
            "tracked_since": None,
            "metrics_updated_at": None,
            "release_downloads_delta_1d": None,
            "clones_14d_delta_1d": None,
            "unique_cloners_14d_delta_1d": None,
            "tracked_total_clones_delta_1d": None,
            "metrics_history": None,
        }
        if repo.lower() == _CCT_REPO:
            project.update(_usage_cache.get(_CCT_REPO, {}))
        out.append(project)
    return out
