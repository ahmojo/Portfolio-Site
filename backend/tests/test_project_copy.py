from __future__ import annotations

from pathlib import Path

from app.db import DEFAULT_CONTENT


ROOT = Path(__file__).parents[2]
PROJECT_SLUGS = {
    "regal-erkennung",
    "codex-claude-transfer",
    "portfolio",
    "cli-agent",
    "machine-learning",
}


def test_every_project_has_a_short_default_writeup_without_em_dashes():
    projects = DEFAULT_CONTENT["projects"]

    assert {project["slug"] for project in projects} == PROJECT_SLUGS
    for project in projects:
        assert project["desc"].strip()
        assert project["content"].strip()
        assert "—" not in project["desc"]
        assert "—" not in project["content"]
        assert len(project["content"].split()) < 140


def test_english_project_fallbacks_are_complete_and_plain():
    locale = (ROOT / "locale.js").read_text(encoding="utf-8")
    project_copy = locale.split("projects: {", 1)[1].split("openSource:", 1)[0]

    for slug in PROJECT_SLUGS:
        assert slug in project_copy
    assert "—" not in project_copy
    assert "## Project" in project_copy
    assert "## Purpose" in project_copy
    assert "## Notebooks" in project_copy
