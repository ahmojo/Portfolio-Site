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
    assert "root.setProperty('--decor-intensity',theme.decoration_intensity/100)" in html
    assert 'data-decoration="none"' in html
    assert 'body[data-decoration="rails"]' in html
    assert 'body[data-decoration="brackets"]' in html
    assert 'body[data-button-style="gradient"]' in html
    assert 'body[data-button-animation="underline"]' in html


def test_legacy_particle_network_cannot_render_or_be_selected():
    public = (ROOT / "index.html").read_text(encoding="utf-8")
    admin = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")

    for retired_fragment in (
        'id="hero-canvas"',
        "hero particle network",
        "__setParticles",
        'data-decoration="particles"',
    ):
        assert retired_fragment not in public

    for retired_fragment in (
        'value="particles"',
        'id="theme-particles"',
        'data-decoration="particles"',
    ):
        assert retired_fragment not in admin

    assert "decoration:'none'" in public
    assert "decoration:'none'" in admin


def test_background_modes_do_not_reintroduce_large_radial_glows():
    public_html = (ROOT / "index.html").read_text(encoding="utf-8")
    admin_html = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")

    for selector, html in (("body", public_html), (r"\.theme-stage", admin_html)):
        for mode in ("ambient", "mesh"):
            match = re.search(
                rf'{selector}\[data-background="{mode}"\]\{{(?P<rule>[^}}]+)\}}',
                html,
            )
            assert match, f"missing CSS rule for {mode!r} background"
            assert "radial-gradient" not in match.group("rule")


def test_public_accent_feedback_has_no_blurred_colored_shadows():
    public_html = (ROOT / "index.html").read_text(encoding="utf-8")
    admin_html = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")

    accent_shadows = [
        shadow
        for shadow in re.findall(r"box-shadow:([^;}]+)", public_html)
        if "acc-rgb" in shadow or "var(--acc)" in shadow
    ]
    assert all("inset" in shadow for shadow in accent_shadows)
    assert "filter:saturate" not in public_html
    assert "@keyframes ping" not in public_html
    assert "@keyframes themeGlow" not in admin_html
    assert "@keyframes themeRing" in admin_html


def test_footer_work_status_is_flat_and_has_no_live_light():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'class="now-bar" id="now-bar" role="status" aria-live="polite"' in html
    assert 'class="now-work"' in html
    assert "live-dot" not in html
    assert "now-pill" not in html
    assert ".now-label::before" in html


def test_preview_opens_the_unsaved_draft_without_publishing():
    admin = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")
    public = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'id="preview-btn"' in admin
    assert "const PREVIEW_STORAGE_PREFIX='portfolio-admin-preview:'" in admin
    assert "localStorage.setItem(PREVIEW_STORAGE_PREFIX+token" in admin
    assert "window.open('/?'+params.toString(),'_blank','noopener')" in admin
    assert admin.count("prepareContentPayload()") >= 2

    assert "const PREVIEW_STORAGE_PREFIX='portfolio-admin-preview:'" in public
    assert "function readAdminPreview()" in public
    assert "const previewContent=readAdminPreview()" in public
    assert "previewContent?Promise.resolve(previewContent)" in public
    assert "previewContent?Promise.resolve([])" in public
    assert "showAdminPreviewNotice()" in public


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
