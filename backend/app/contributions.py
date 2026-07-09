"""GitHub contributions + activity aggregation.

Builds the "GitHub stats" you see on the site:
  - current commit streak (consecutive days with commits, counting back from today)
  - longest streak ever
  - total commits this year
  - per-day contribution counts for this year (for a heatmap / chart)

Sources, tried in order:
  1. CONTRIBUTION CALENDAR SCRAPE (token-free, full year, accurate counts)
     GitHub renders the full-year calendar server-side at
     /users/{user}/contributions — each day has data-date + data-level +
     a screen-reader span with the exact count.
  2. GraphQL contributionsCollection (needs a token, full year)
  3. REST public events API (token-free, ~90 days only) — last resort.

This calendar scrape is the default and gives the same numbers you see on
your GitHub profile.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from collections import defaultdict
from datetime import datetime, timezone

import httpx

from .config import settings

log = logging.getLogger("portfolio.contrib")

_GH_API = "https://api.github.com"

_cache: dict = {}          # {"data": {...}, "ts": float}
_lock = asyncio.Lock()
TTL = 600  # 10 min

# regex to find each calendar day cell
_DAY_RE = re.compile(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"')
_COUNT_RE = re.compile(r'(\d+)\s+contribution')


def _headers() -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "portfolio-backend/1.0",
    }
    if settings.github_token:
        h["Authorization"] = f"Bearer {settings.github_token}"
    return h


def _browser_headers() -> dict[str, str]:
    """Headers that look like a real browser — needed for the calendar HTML."""
    h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    return h


async def _via_calendar(client: httpx.AsyncClient) -> dict | None:
    """Scrape the full-year contribution calendar. Token-free + accurate."""
    try:
        r = await client.get(
            f"https://github.com/users/{settings.github_user}/contributions",
            headers=_browser_headers(), timeout=12.0, follow_redirects=True,
        )
        if r.status_code != 200:
            log.warning("calendar scrape returned %s", r.status_code)
            return None
        html = r.text

        daily: dict[str, int] = {}
        for m in _DAY_RE.finditer(html):
            date, _level = m.group(1), int(m.group(2))
            seg = html[m.end():m.end() + 400]
            cm = _COUNT_RE.search(seg)
            daily[date] = int(cm.group(1)) if cm else 0

        if not daily:
            return None

        # the calendar rolls on a 365-day window ending today, so filter to
        # the current calendar year for the "this year" totals.
        year = datetime.now(timezone.utc).year
        year_daily = {d: c for d, c in daily.items() if d.startswith(str(year))}
        current, longest = _streaks(daily)   # streak over the full window
        total_year = sum(year_daily.values())

        return {
            "source": "calendar",
            "year": year,
            "total_commits": total_year,
            "commits_this_year": total_year,
            "current_streak": current,
            "longest_streak": longest,
            "daily": year_daily,
            "active_days": sum(1 for c in year_daily.values() if c > 0),
        }
    except Exception as e:
        log.warning("calendar scrape failed: %s", e)
        return None


async def _via_graphql(client: httpx.AsyncClient) -> dict | None:
    """GraphQL contributionsCollection — accurate, full year. Needs a token."""
    if not settings.github_token:
        return None
    now = datetime.now(timezone.utc)
    year = now.year
    from_dt = f"{year}-01-01T00:00:00Z"
    to = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    query = """
    query($login:String!,$from:DateTime!,$to:DateTime!){
      user(login:$login){
        contributionsCollection(from:$from,to:$to){
          contributionCalendar{ totalContributions weeks{ days{ contributionCount date } } }
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
        }
        repositories(privacy:PUBLIC,first:1,orderBy:{field:UPDATED_AT,direction:DESC}){ totalCount }
        followers{ totalCount }
      }
    }"""
    try:
        r = await client.post(
            f"{_GH_API}/graphql",
            json={"query": query, "variables": {"login": settings.github_user, "from": from_dt, "to": to}},
            headers=_headers(), timeout=10.0,
        )
        r.raise_for_status()
        data = r.json()
        user = data.get("data", {}).get("user")
        if not user:
            return None
        cal = user["contributionsCollection"]["contributionCalendar"]
        daily = {d["date"]: d["contributionCount"] for w in cal["weeks"] for d in w["days"]}
        current, longest = _streaks(daily)
        return {
            "source": "graphql",
            "year": year,
            "total_commits": cal["totalContributions"],
            "commits_this_year": user["contributionsCollection"]["totalCommitContributions"],
            "public_repos": user["repositories"]["totalCount"],
            "followers": user["followers"]["totalCount"],
            "pull_requests": user["contributionsCollection"]["totalPullRequestContributions"],
            "issues": user["contributionsCollection"]["totalIssueContributions"],
            "current_streak": current,
            "longest_streak": longest,
            "daily": daily,
            "active_days": sum(1 for c in daily.values() if c > 0),
        }
    except Exception as e:
        log.warning("graphql contributions failed: %s", e)
        return None


async def _via_rest(client: httpx.AsyncClient) -> dict:
    """Last-resort fallback: public REST events API. Token-free, ~90 days only."""
    events: list[dict] = []
    async def page(p):
        r = await client.get(
            f"{_GH_API}/users/{settings.github_user}/events/public",
            params={"per_page": 100, "page": p}, headers=_headers(), timeout=8.0,
        )
        return r.json() if r.status_code == 200 else []
    results = await asyncio.gather(*[page(p) for p in range(1, 11)])
    for batch in results:
        events.extend(batch)

    year = datetime.now(timezone.utc).year
    daily: dict[str, int] = defaultdict(int)
    for ev in events:
        ts = ev.get("created_at", "")
        if not ts or not ts.startswith(str(year)):
            continue
        etype = ev.get("type")
        if etype == "PushEvent":
            daily[ts[:10]] += len(ev.get("payload", {}).get("commits", []))
        elif etype in ("CreateEvent", "PullRequestEvent", "IssuesEvent"):
            daily[ts[:10]] += 1

    current, longest = _streaks(daily)
    pub = foll = 0
    try:
        u = await client.get(f"{_GH_API}/users/{settings.github_user}", headers=_headers(), timeout=8.0)
        if u.status_code == 200:
            pub = u.json().get("public_repos", 0)
            foll = u.json().get("followers", 0)
    except Exception:
        pass

    return {
        "source": "rest-events",
        "note": "approximate — public events only cover ~90 days; set a token for full-year accuracy.",
        "year": year,
        "total_commits": sum(daily.values()),
        "commits_this_year": sum(daily.values()),
        "public_repos": pub,
        "followers": foll,
        "pull_requests": 0,
        "issues": 0,
        "current_streak": current,
        "longest_streak": longest,
        "daily": dict(daily),
        "active_days": sum(1 for c in daily.values() if c > 0),
    }


def _parse(iso: str):
    return datetime.strptime(iso, "%Y-%m-%d").date()


def _streaks(daily: dict[str, int]) -> tuple[int, int]:
    """Return (current_streak, longest_streak) over a {date:count} map."""
    dates = sorted(d for d, c in daily.items() if c > 0)
    if not dates:
        return 0, 0

    # longest run of consecutive days
    longest = run = 1
    for i in range(1, len(dates)):
        gap = (_parse(dates[i]) - _parse(dates[i - 1])).days
        if gap == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    # current streak: walk back from today (allow today to be empty)
    today = datetime.now(timezone.utc).date()
    start = today
    if daily.get(start.isoformat(), 0) == 0:
        start = today - _timedelta(1)
    current = 0
    cur = start
    while daily.get(cur.isoformat(), 0) > 0:
        current += 1
        cur = cur - _timedelta(1)
    return current, longest


def _timedelta(days: int):
    from datetime import timedelta
    return timedelta(days=days)


async def get_stats() -> dict:
    """Return contribution stats, trying sources in order, cached for TTL."""
    now = time.time()
    async with _lock:
        if _cache and now - _cache["ts"] < TTL:
            return _cache["data"]

    async with httpx.AsyncClient() as client:
        data = (
            await _via_calendar(client)   # token-free, full year
            or await _via_graphql(client)  # needs token
            or await _via_rest(client)     # last resort, ~90 days
        )

    # always try to enrich with profile counts (repos/followers) cheaply
    if "public_repos" not in data:
        try:
            async with httpx.AsyncClient() as client:
                u = await client.get(f"{_GH_API}/users/{settings.github_user}", headers=_headers(), timeout=8.0)
                if u.status_code == 200:
                    data["public_repos"] = u.json().get("public_repos", 0)
                    data["followers"] = u.json().get("followers", 0)
        except Exception:
            pass

    data.setdefault("public_repos", 0)
    data.setdefault("followers", 0)
    data.setdefault("pull_requests", 0)
    data.setdefault("issues", 0)
    data.setdefault("active_days", 0)

    async with _lock:
        _cache["data"] = data
        _cache["ts"] = now
    return data
