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

PROBLEM_PROJECTS = {"regal-erkennung", "codex-claude-transfer"}
EXPECTED_HEADINGS = {
    "regal-erkennung": ["## Problem", "## Architektur", "## Stand"],
    "codex-claude-transfer": ["## Problem", "## Architektur", "## Nutzung"],
    "portfolio": ["## Architektur", "## Nutzung", "## Betrieb"],
    "cli-agent": ["## Architektur", "## Nutzung", "## Stand"],
    "machine-learning": ["## Architektur", "## Projekt", "## Datensatz", "## Stand"],
}
EN_HEADINGS = {
    "regal-erkennung": ["## Problem", "## Architecture", "## Status"],
    "codex-claude-transfer": ["## Problem", "## Architecture", "## Usage"],
    "portfolio": ["## Architecture", "## Usage", "## Hosting"],
    "cli-agent": ["## Architecture", "## Usage", "## Status"],
    "machine-learning": ["## Architecture", "## Project", "## Dataset", "## Status"],
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


def test_default_writeups_start_with_the_right_problem_and_architecture_order():
    projects = {project["slug"]: project for project in DEFAULT_CONTENT["projects"]}

    for slug, headings in EXPECTED_HEADINGS.items():
        content = projects[slug]["content"]
        positions = [content.index(heading) for heading in headings]
        assert positions == sorted(positions)
        assert ("## Problem" in content) is (slug in PROBLEM_PROJECTS)


def test_controller_copy_matches_short_project_descriptions_without_em_dashes():
    controller = (ROOT / "locale-controller.js").read_text(encoding="utf-8")
    project_copy = controller.split("{selector:'.projs .proj:nth-child(1)", 1)[1].split(
        "{selector:'#opensource", 1
    )[0]

    assert project_copy.count(".proj-desc") == len(PROJECT_SLUGS)
    assert "—" not in project_copy
    for phrase in (
        "eingerichtete Regalplätze",
        "prüft die Prüfsumme",
        "geschützter Admin-Bereich",
        "./calculator",
        "Datenprüfung",
    ):
        assert phrase in project_copy


def test_english_project_fallbacks_are_complete_and_plain():
    locale = (ROOT / "locale.js").read_text(encoding="utf-8")
    project_copy = locale.split("projects: {", 1)[1].split("openSource:", 1)[0]

    for slug in PROJECT_SLUGS:
        assert slug in project_copy
    assert "—" not in project_copy
    for slug, headings in EN_HEADINGS.items():
        marker = next(
            marker for marker in (f"'{slug}':", f"{slug}:") if marker in project_copy
        )
        start = project_copy.index(marker)
        next_project = project_copy.find("      },", start)
        content = project_copy[start:next_project if next_project != -1 else None]
        positions = [content.index(heading) for heading in headings]
        assert positions == sorted(positions)
        assert ("## Problem" in content) is (slug in PROBLEM_PROJECTS)
