from pathlib import Path
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).parents[2]


def test_admin_theme_studio_exposes_complete_customization_controls():
    admin = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")

    for control_id in (
        "theme-surface",
        "theme-accent-alt",
        "theme-background-style",
        "theme-decoration",
        "theme-decoration-intensity",
        "theme-button-style",
        "theme-button-animation",
        "theme-gradient-angle",
        "theme-radius",
        "theme-content-width",
        "theme-motion",
        "theme-grain",
    ):
        assert f'id="{control_id}"' in admin

    for option in ("rails", "brackets", "aurora", "gradient", "glass", "underline"):
        assert f'value="{option}"' in admin

    assert "siteContent.theme={...THEME_DEFAULTS,...(siteContent.theme||{})}" in admin
    assert "data-theme-preset=\"paper\"" in admin
    assert 'id="theme-stage"' in admin


def test_public_site_applies_palette_layout_motion_buttons_and_decoration():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "root.setProperty('--bg-1',theme.surface)" in html
    assert "root.setProperty('--line',mixHex(theme.bg,theme.ink,.16))" in html
    assert "root.setProperty('--maxw',theme.content_width+'px')" in html
    assert "document.body.dataset.background=theme.background_style" in html
    assert "document.body.dataset.decoration=theme.decoration" in html
    assert "document.body.dataset.buttonStyle=theme.button_style" in html
    assert "document.body.dataset.buttonAnimation" in html
    assert "intensity:theme.decoration_intensity/100" in html
    assert 'data-decoration="particles"' in html
    assert 'body[data-decoration="rails"]' in html
    assert 'body[data-decoration="brackets"]' in html
    assert 'body[data-button-style="gradient"]' in html
    assert 'body[data-button-animation="underline"]' in html


def test_old_terminal_exit_footer_is_removed():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "ahmet@portfolio:~$" not in html
    assert "foot-cursor" not in html
    assert "© Ahmet Faruk Ilhan" in html


def test_admin_inline_script_has_valid_javascript():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed")

    admin = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")
    scripts = re.findall(
        r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>",
        admin,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert scripts
    for script in scripts:
        result = subprocess.run(
            [node, "--check", "-"],
            input=script,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
