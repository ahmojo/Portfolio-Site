"""Pydantic request/response models shared across routers."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field


# ─── projects ─────────────────────────────────────────────────
class ProjectOut(BaseModel):
    name: str
    repo: str
    url: str
    stars: int
    forks: int = 0
    language: Optional[str] = None
    updated_at: Optional[str] = None  # ISO from GitHub
    description: Optional[str] = None
    exists: bool = True
    cached: bool = False
    fetched_at: Optional[Union[float, str]] = None


# ─── now ──────────────────────────────────────────────────────
class NowOut(BaseModel):
    status: str
    detail: str
    updated_at: str


class NowIn(BaseModel):
    status: str = Field(..., min_length=1, max_length=80, strip_whitespace=True)
    detail: str = Field("", max_length=280, strip_whitespace=True)
    token: str = ""


# ─── github stats / contributions ─────────────────────────────
class GithubStatsOut(BaseModel):
    source: str = "rest-events"
    note: Optional[str] = None
    year: int
    total_commits: int = 0
    commits_this_year: int = 0
    public_repos: int = 0
    followers: int = 0
    pull_requests: int = 0
    issues: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    daily: dict[str, int] = {}
    top_repos: Optional[list[dict]] = None


# ─── site content (editable via /admin) ───────────────────────
class HeroContent(BaseModel):
    name: str = "Ahmet"
    lede: str = ""
    phrases: list[str] = []

class NowContent(BaseModel):
    status: str = ""
    detail: str = ""

class AboutContent(BaseModel):
    paragraphs: list[str] = []

class StatItem(BaseModel):
    value: str = "0"
    suffix: Optional[str] = None      # e.g. "nd", "+"
    decorator: Optional[str] = None   # "dot" renders the green dot
    label: str = ""

class SkillRow(BaseModel):
    key: str = ""
    items: list[str] = []

class ProjBadge(BaseModel):
    label: str = ""
    variant: str = "py"   # hack | cv | ml | py | (none)

class ProjectItem(BaseModel):
    title: str = ""
    desc: str = ""
    stack: str = ""
    repo: str = ""
    featured: bool = False
    media: Optional[str] = None
    badges: list[ProjBadge] = []
    slug: str = ""                 # url-safe id for /p/{slug} deep-dive page
    content: str = ""              # markdown body for the deep-dive (optional)


OPEN_SOURCE_DEFAULTS = (
    {
        "repo": "nushell/nushell",
        "pr": 18666,
        "title": "Parser-Scope-Leak behoben",
        "desc": "Scope-Verlust bei Interpolation behoben und Regressionstests ergänzt.",
        "tech": "Rust · Parser",
    },
    {
        "repo": "pygments/pygments",
        "pr": 3180,
        "title": "CSS-Farbe erweitert",
        "desc": "transparent in Styles und HTML-Ausgabe unterstützt und getestet.",
        "tech": "Python · pytest",
    },
    {
        "repo": "go-git/go-git",
        "pr": 2248,
        "title": "Gitignore-API erklärt",
        "desc": "Pfade, Verzeichnisse und Match-Priorität präziser dokumentiert.",
        "tech": "Go · API Docs",
    },
)


class OpenSourceItem(BaseModel):
    repo: str = Field("", max_length=160, strip_whitespace=True)
    pr: int = Field(1, ge=1, le=999_999_999)
    title: str = Field("", max_length=120, strip_whitespace=True)
    desc: str = Field("", max_length=280, strip_whitespace=True)
    tech: str = Field("", max_length=100, strip_whitespace=True)


class LearnItem(BaseModel):
    kind: str = "Course"          # "Project" or "Course"
    name: str = ""
    date: str = ""
    type: str = "url"             # "url" or "preview"
    url: Optional[str] = None
    src: Optional[str] = None
    title: Optional[str] = None

class ThemeContent(BaseModel):
    bg: str = "#161a28"
    accent: str = "#6de6a2"
    ink: str = "#e6edf8"
    particles: int = 72

class SiteContent(BaseModel):
    hero: HeroContent = HeroContent()
    now: NowContent = NowContent()
    about: AboutContent = AboutContent()
    stats: list[StatItem] = []
    skills: list[SkillRow] = []
    projects: list[ProjectItem] = []
    open_source: list[OpenSourceItem] = Field(
        default_factory=lambda: [
            OpenSourceItem(**item) for item in OPEN_SOURCE_DEFAULTS
        ]
    )
    learning: list[LearnItem] = []
    theme: ThemeContent = ThemeContent()
