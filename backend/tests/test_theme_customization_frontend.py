from pathlib import Path
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).parents[2]


def _assert_only_crisp_inset_shadows(rule: str) -> None:
    match = re.search(r"box-shadow:(?P<value>[^;]+)", rule)
    assert match, "missing box-shadow declaration"
    layers = []
    start = 0
    depth = 0
    value = match.group("value")
    for index, char in enumerate(value):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            layers.append(value[start:index].strip())
            start = index + 1
    layers.append(value[start:].strip())
    assert layers
    assert all(layer.startswith("inset ") for layer in layers), layers


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

    for option in ("rails", "grid", "brackets", "gradient", "glass", "underline"):
        assert f'value="{option}"' in admin

    assert "siteContent.theme=normalizeTheme(siteContent.theme)" in admin
    assert "data-theme-preset=\"paper\"" in admin
    assert 'id="theme-stage"' in admin


def test_public_site_applies_palette_layout_motion_buttons_and_decoration():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "root.setProperty('--bg-1',theme.surface)" in html
    assert "root.setProperty('--line',mixHex(theme.bg,theme.ink,.16))" in html
    assert "root.setProperty('--maxw',theme.content_width+'px')" in html
    assert "document.body.dataset.background=theme.background_style" in html
    assert "const safeDecoration=['rails','grid','brackets'].includes(theme.decoration)?theme.decoration:'none'" in html
    assert "document.body.dataset.decoration=safeDecoration" in html
    assert "document.body.dataset.buttonStyle=theme.button_style" in html
    assert "document.body.dataset.buttonAnimation" in html
    assert "root.setProperty('--decor-intensity',theme.decoration_intensity/100)" in html
    assert 'data-decoration="none"' in html
    assert 'body[data-decoration="rails"]' in html
    assert 'body[data-decoration="brackets"]' in html
    assert 'body[data-button-style="gradient"]' in html
    assert 'body[data-button-animation="underline"]' in html


def test_unsafe_legacy_decorations_cannot_render_or_be_selected():
    public = (ROOT / "index.html").read_text(encoding="utf-8")
    admin = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")

    for retired_fragment in (
        'id="hero-canvas"',
        "hero particle network",
        "__setParticles",
        'data-decoration="particles"',
        'data-decoration="aurora"',
        "filter:blur(90px)",
    ):
        assert retired_fragment not in public

    for retired_fragment in (
        'value="particles"',
        'id="theme-particles"',
        'data-decoration="particles"',
        'value="aurora"',
        'data-decoration="aurora"',
        "themeAurora",
    ):
        assert retired_fragment not in admin

    assert "decoration:'none'" in public
    assert "decoration:'none'" in admin
    assert 'data-decoration="brackets"' in public
    assert 'value="brackets"' in admin
    assert 'data-decoration="brackets"' in admin
    assert public.count('<span></span>') >= 4


def test_background_modes_do_not_reintroduce_large_radial_glows():
    public_html = (ROOT / "index.html").read_text(encoding="utf-8")
    admin_html = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")

    for mode in ("ambient", "mesh"):
        public_selector = (
            f'body[data-background="{mode}"]'
            if mode == "ambient"
            else f'body[data-background="{mode}"] #hero'
        )
        for selector, html in (
            (public_selector, public_html),
            (f'.theme-stage[data-background="{mode}"]', admin_html),
        ):
            match = re.search(
                re.escape(selector) + r'\{(?P<rule>[^}]+)\}',
                html,
            )
            assert match, f"missing CSS rule for {mode!r} background"
            assert "radial-gradient" not in match.group("rule")


def test_patterned_background_effects_are_bounded_to_the_hero():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'body[data-background="ambient"]{' in html
    assert 'body[data-background="mesh"] #hero{' in html
    assert "body::before" not in html
    assert "#hero::after{content:'';position:absolute" in html
    assert "position:fixed;inset:0;z-index:0;pointer-events:none;opacity:var(--grain-opacity)" not in html


def test_ambient_background_is_a_uniform_opaque_tint_without_banding():
    public_html = (ROOT / "index.html").read_text(encoding="utf-8")
    admin_html = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")

    public_rule = re.search(
        re.escape('body[data-background="ambient"]') + r'\{(?P<rule>[^}]+)\}',
        public_html,
    )
    admin_rule = re.search(
        re.escape('.theme-stage[data-background="ambient"]') + r'\{(?P<rule>[^}]+)\}',
        admin_html,
    )
    assert public_rule and admin_rule
    for rule, background_var, accent_var in (
        (public_rule.group("rule"), "var(--bg)", "var(--acc)"),
        (admin_rule.group("rule"), "var(--pv-bg)", "var(--pv-acc)"),
    ):
        assert "gradient" not in rule
        assert "transparent" not in rule
        assert "color-mix" in rule
        assert f"{background_var} 98%" in rule
        assert f"{accent_var} 2%" in rule


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


def test_featured_project_keeps_safe_illumination_without_composited_highlight_layer():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert ".proj.feat::before{display:none}" in html
    assert ".proj.feat:hover .feat-media video" not in html
    assert "filter:brightness" not in html

    featured = re.search(r"\.proj\.feat\{(?P<rule>[^}]+)\}", html)
    featured_hover = re.search(r"\.proj\.feat:hover\{(?P<rule>[^}]+)\}", html)
    assert featured and featured_hover
    assert "gradient" not in featured.group("rule")
    assert "gradient" not in featured_hover.group("rule")
    assert "background-color:color-mix" in featured.group("rule")
    assert "border:1px solid rgba(var(--acc-rgb),.2)" in featured.group("rule")
    assert "box-shadow:inset 3px 0 0" in featured.group("rule")
    _assert_only_crisp_inset_shadows(featured.group("rule"))
    _assert_only_crisp_inset_shadows(featured_hover.group("rule"))
    assert "padding:26px 22px 28px" in featured.group("rule")
    assert "padding-left:22px" in featured_hover.group("rule")


def test_project_and_merge_card_highlights_use_flat_surfaces_without_blur_layers():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    project_hover = re.search(r"\.proj:hover\{(?P<rule>[^}]+)\}", html)
    merge_card = re.search(r"\.oss-card\{(?P<rule>[^}]+)\}", html)
    merge_hover = re.search(
        r"\.oss-card:hover,\s*\.oss-card:focus-visible\{(?P<rule>[^}]+)\}",
        html,
    )
    assert project_hover and merge_card and merge_hover
    assert "gradient" not in project_hover.group("rule")
    assert "gradient" not in merge_card.group("rule")
    assert "transform" not in merge_card.group("rule")
    assert "translateY" not in merge_hover.group("rule")
    assert "box-shadow:inset 3px 0 0" in merge_hover.group("rule")
    _assert_only_crisp_inset_shadows(merge_hover.group("rule"))
    assert "background-color:var(--bg)" in project_hover.group("rule")
    assert ".reveal .oss-card[data-stagger]{transition:" in html
    assert "background-color var(--t),border-color var(--t),box-shadow var(--t)" in html


def test_admin_inline_preview_uses_the_same_opaque_featured_highlight_path():
    admin = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")

    card = re.search(r"\.theme-preview-card\{(?P<rule>[^}]+)\}", admin)
    assert card
    rule = card.group("rule")
    assert "background:var(--pv-bg)" in rule
    assert "var(--pv-bg) 94%" in rule
    assert "var(--pv-acc) 6%" in rule
    assert "gradient" not in rule
    _assert_only_crisp_inset_shadows(rule)


def test_standard_project_separators_cannot_inherit_card_rounding():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    project = re.search(r"\.proj\{(?P<rule>[^}]+)\}", html)
    featured = re.search(r"\.proj\.feat\{(?P<rule>[^}]+)\}", html)
    assert project and featured
    assert "border-radius:0" in project.group("rule")
    assert "border-radius:var(--radius)" in featured.group("rule")
    assert ".proj,.gh-panel" not in html


def test_footer_work_status_is_framed_and_has_no_live_light():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'class="now-bar" id="now-bar" role="status" aria-live="polite"' in html
    assert 'class="now-work"' in html
    assert "live-dot" not in html
    assert "now-pill" not in html
    assert ".now-bar .now-label::before{content:'//'" in html

    bar = re.search(r"\.now-bar\{(?P<rule>[^}]+)\}", html)
    assert bar
    assert "border:1px solid var(--line-2)" in bar.group("rule")
    assert "background:rgba(var(--surface-rgb),.12)" in bar.group("rule")
    assert "box-shadow:none" in bar.group("rule")
    assert ".now-bar::before" in html


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
