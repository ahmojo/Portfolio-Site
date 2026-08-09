"""GitHub client + in-memory cache.

Keeps the project list responsive and avoids hammering the GitHub API
(anonymous rate limit is 60 req/h per IP).
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import date
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
                return total
            page += 1
    except Exception as exc:
        log.warning("GitHub release fetch failed for %s: %s", repo, exc)
        return None


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
        result["release_downloads"] = release_downloads
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
