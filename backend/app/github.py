"""GitHub client + in-memory cache.

Keeps the project list responsive and avoids hammering the GitHub API
(anonymous rate limit is 60 req/h per IP).
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Optional

import httpx

from .config import settings

log = logging.getLogger("portfolio.github")

_GH_API = "https://api.github.com"

_cache: dict[str, dict] = {}          # repo -> data
_cache_ts: dict[str, float] = {}      # repo -> fetch timestamp
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

    out = []
    for name, original, repo in configured:
        data = _cache.get(repo, {})
        out.append({
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
        })
    return out
