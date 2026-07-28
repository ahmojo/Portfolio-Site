"""Discover merged open-source pull requests for the configured GitHub user."""
from __future__ import annotations

import asyncio
import html
import logging
import re
import time
from typing import Any

import httpx

from .config import settings

log = logging.getLogger("portfolio.open_source")

_GH_API = "https://api.github.com"
_MAX_SEARCH_PAGES = 10
_TITLE_PREFIX_RE = re.compile(
    r"^(?:build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)"
    r"(?:\([^)]+\))?!?:\s*",
    re.IGNORECASE,
)
_ISSUE_REFERENCE_RE = re.compile(
    r"^(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#\d+[\s.,;:!-]*$",
    re.IGNORECASE,
)
_LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]+\)")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_CHECKBOX_RE = re.compile(r"^\s*[-*+]\s+\[[ xX]\]\s+")
_PREFERRED_SECTIONS = ("summary", "description", "solution", "why", "what changed")
_IGNORED_LABEL_PARTS = {
    "approved",
    "backport",
    "blocked",
    "duplicate",
    "good first issue",
    "help wanted",
    "needs review",
    "priority",
    "ready",
    "size",
    "status",
    "triage",
    "wip",
}
_IGNORED_TOPICS = {"hacktoberfest", "open-source", "open source", "github"}
_LABEL_ALIASES = {
    "bug": "Bug fix",
    "bugfix": "Bug fix",
    "documentation": "Docs",
    "docs": "Docs",
    "enhancement": "Enhancement",
    "testing": "Testing",
    "tests": "Testing",
}

_cache: list[dict[str, Any]] = []
_cache_at = 0.0
_cache_lock = asyncio.Lock()


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ahmojo-portfolio",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


def _shorten(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    shortened = value[: limit + 1].rsplit(" ", 1)[0].rstrip(".,;: -")
    return f"{shortened}\u2026" if shortened else f"{value[: limit - 1]}\u2026"


def short_title(title: str) -> str:
    """Turn a PR title into a compact card title without inventing wording."""
    cleaned = _TITLE_PREFIX_RE.sub("", html.unescape(title or "")).strip()
    cleaned = cleaned or html.unescape(title or "").strip() or "Merged contribution"
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return _shorten(cleaned, 120)


def _clean_markdown_line(line: str) -> str:
    line = _CHECKBOX_RE.sub("", line)
    line = _BULLET_RE.sub("", line)
    line = _LINK_RE.sub(r"\1", line)
    line = re.sub(r"</?[^>]+>", " ", line)
    line = re.sub(r"[*~`]", "", line)
    return re.sub(r"\s+", " ", html.unescape(line)).strip()


def _meaningful(line: str) -> bool:
    if not line or line.startswith("|") or _ISSUE_REFERENCE_RE.fullmatch(line):
        return False
    lowered = line.lower()
    return not (
        lowered.startswith(("http://", "https://"))
        or lowered in {"n/a", "none", "not applicable"}
        or len(line) < 18
    )


def _body_sections(body: str) -> tuple[dict[str, list[str]], list[str]]:
    text = _HTML_COMMENT_RE.sub("", body or "")
    text = _CODE_BLOCK_RE.sub("", text)
    sections: dict[str, list[str]] = {"": []}
    all_lines: list[str] = []
    current = ""
    paragraph: list[str] = []

    def append_paragraph() -> None:
        if not paragraph:
            return
        cleaned = _clean_markdown_line(" ".join(paragraph))
        paragraph.clear()
        if _meaningful(cleaned):
            sections.setdefault(current, []).append(cleaned)
            all_lines.append(cleaned)

    for raw_line in text.splitlines():
        heading = _HEADING_RE.match(raw_line)
        if heading:
            append_paragraph()
            current = _clean_markdown_line(heading.group(1)).lower()
            sections.setdefault(current, [])
            continue
        if not raw_line.strip():
            append_paragraph()
        elif _CHECKBOX_RE.match(raw_line) or _BULLET_RE.match(raw_line):
            append_paragraph()
            paragraph.append(raw_line)
            append_paragraph()
        else:
            paragraph.append(raw_line)
    append_paragraph()
    return sections, all_lines


def short_description(body: str, title: str) -> str:
    """Extract factual prose from common PR template sections."""
    sections, all_lines = _body_sections(body)
    candidates: list[str] = []
    for preferred in _PREFERRED_SECTIONS:
        for heading, lines in sections.items():
            if heading == preferred or heading.startswith(f"{preferred} "):
                candidates.extend(lines[:2])
        if candidates:
            break
    if not candidates:
        candidates = all_lines[:2]

    description = " ".join(candidates)
    if not description:
        description = f"Merged contribution: {short_title(title).rstrip('.')}"
    if description[-1:] not in ".!?":
        description += "."
    return _shorten(description, 280)


def _metadata_tag(raw_name: str) -> str:
    lowered = raw_name.lower()
    if re.match(r"^[a-z]{1,3}[:-]", lowered):
        raw_name = raw_name[2:]
    return raw_name.replace("-", " ").strip().title()


def technology_label(
    repository: dict[str, Any], labels: list[dict[str, Any]]
) -> str:
    """Build a deterministic technology label from GitHub metadata."""
    parts: list[str] = []
    language = str(repository.get("language") or "").strip()
    if language:
        parts.append(language)

    for label in labels:
        raw_name = str(label.get("name") or "").strip()
        lowered = raw_name.lower()
        if (
            not raw_name
            or any(part in lowered for part in _IGNORED_LABEL_PARTS)
            or raw_name.casefold() in {part.casefold() for part in parts}
        ):
            continue
        display = _LABEL_ALIASES.get(lowered, _metadata_tag(raw_name))
        parts.append(display)
        break

    if len(parts) == 1:
        topics = repository.get("topics") or []
        for topic in topics:
            raw_topic = str(topic).strip()
            if raw_topic.lower() in _IGNORED_TOPICS:
                continue
            display = _metadata_tag(raw_topic)
            if display and display.casefold() != parts[0].casefold():
                parts.append(display)
                break
    return _shorten(" \u00b7 ".join(parts) or "Open source", 100)


def _repo_from_item(item: dict[str, Any]) -> str:
    prefix = f"{_GH_API}/repos/"
    repository_url = str(item.get("repository_url") or "")
    if not repository_url.startswith(prefix):
        return ""
    parts = repository_url.removeprefix(prefix).strip("/").split("/")
    return "/".join(parts[:2]) if len(parts) >= 2 else ""


async def _repository_metadata(
    client: httpx.AsyncClient, repo: str
) -> tuple[str, dict[str, Any]]:
    try:
        response = await client.get(
            f"{_GH_API}/repos/{repo}", headers=_headers(), timeout=8.0
        )
        if response.status_code == 200:
            return repo, response.json()
        log.warning(
            "GitHub repository metadata returned %s for %s",
            response.status_code,
            repo,
        )
    except httpx.HTTPError as exc:
        log.warning("GitHub repository metadata failed for %s: %s", repo, exc)
    return repo, {}


async def fetch_open_source(
    client: httpx.AsyncClient,
    *,
    user: str,
    excluded_owners: list[str],
) -> list[dict[str, Any]]:
    """Fetch, filter, and format merged PRs from GitHub."""
    excluded = {owner.casefold() for owner in excluded_owners}
    excluded.add(user.casefold())
    negative_owners = " ".join(f"-user:{owner}" for owner in sorted(excluded))
    query = f"author:{user} is:pr is:merged {negative_owners}"

    found: list[dict[str, Any]] = []
    for page in range(1, _MAX_SEARCH_PAGES + 1):
        response = await client.get(
            f"{_GH_API}/search/issues",
            headers=_headers(),
            params={
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": 100,
                "page": page,
            },
            timeout=12.0,
        )
        response.raise_for_status()
        batch = response.json().get("items", [])
        found.extend(batch)
        if len(batch) < 100:
            break

    filtered: list[tuple[str, dict[str, Any]]] = []
    for item in found:
        repo = _repo_from_item(item)
        owner = repo.partition("/")[0]
        if repo and owner.casefold() not in excluded:
            filtered.append((repo, item))

    repositories = sorted({repo for repo, _ in filtered})
    metadata = dict(
        await asyncio.gather(
            *[_repository_metadata(client, repo) for repo in repositories]
        )
    )

    filtered.sort(
        key=lambda pair: str(
            pair[1].get("closed_at") or pair[1].get("updated_at") or ""
        ),
        reverse=True,
    )
    return [
        {
            "repo": repo,
            "pr": int(item["number"]),
            "title": short_title(str(item.get("title") or "")),
            "desc": short_description(
                str(item.get("body") or ""), str(item.get("title") or "")
            ),
            "tech": technology_label(
                metadata.get(repo, {}), item.get("labels") or []
            ),
            "synced": True,
        }
        for repo, item in filtered
    ]


def contribution_key(item: dict[str, Any]) -> str:
    """Return the stable owner/repo#number identity used by admin overrides."""
    repo = str(item.get("repo") or "").strip().strip("/").casefold()
    try:
        number = int(item.get("pr") or 0)
    except (TypeError, ValueError):
        return ""
    if repo.count("/") != 1 or number < 1:
        return ""
    return f"{repo}#{number}"


def merge_open_source(
    live_items: list[dict[str, Any]],
    saved_items: list[dict[str, Any]],
    hidden_keys: list[str],
) -> list[dict[str, Any]]:
    """Merge GitHub discoveries with editable, ordered admin content."""
    hidden = {key.strip().casefold() for key in hidden_keys if key.strip()}
    live_by_key = {
        contribution_key(item): {**item, "synced": True}
        for item in live_items
        if contribution_key(item)
    }
    merged_items: list[dict[str, Any]] = []
    used: set[str] = set()

    for saved in saved_items:
        key = contribution_key(saved)
        if key and (key in hidden or key in used):
            continue
        if key in live_by_key:
            item = dict(live_by_key[key])
            for field in ("title", "desc", "tech"):
                if field in saved:
                    item[field] = str(saved.get(field) or "")
            item["synced"] = True
            merged_items.append(item)
            used.add(key)
        else:
            merged_items.append(dict(saved))
            if key:
                used.add(key)

    for live in live_items:
        key = contribution_key(live)
        if not key or key in hidden or key in used:
            continue
        merged_items.append({**live, "synced": True})
        used.add(key)

    return merged_items


async def get_open_source() -> list[dict[str, Any]]:
    """Return a cached live list, preserving the last good result on failure."""
    global _cache, _cache_at
    now = time.monotonic()
    if _cache_at and now - _cache_at < settings.open_source_ttl:
        return [dict(item) for item in _cache]

    async with _cache_lock:
        now = time.monotonic()
        if _cache_at and now - _cache_at < settings.open_source_ttl:
            return [dict(item) for item in _cache]
        try:
            async with httpx.AsyncClient() as client:
                items = await fetch_open_source(
                    client,
                    user=settings.github_user,
                    excluded_owners=settings.open_source_excluded_owners,
                )
            _cache = items
            _cache_at = time.monotonic()
            return [dict(item) for item in items]
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            log.warning("GitHub open-source sync failed: %s", exc)
        return [dict(item) for item in _cache]
