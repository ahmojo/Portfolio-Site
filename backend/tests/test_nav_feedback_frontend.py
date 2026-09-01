from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_navbar_has_clean_links_and_explicit_flag_locale_controls():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'class="nav-index"' not in html
    assert 'data-locale="de"' in html
    assert 'data-locale="en"' in html
    assert html.count('class="locale-flag"') == 2
    assert 'fill="#d52b1e"' in html
    assert 'fill="#143a78"' in html
    assert "min-height:58px" in html
    assert 'class="nav-primary"' in html
    assert "clip-path:polygon(14px 0,100% 0,calc(100% - 14px) 100%,0 100%)" in html
    assert "border-radius:0" in html
    assert "width:100%;margin:0" in html
    assert "main{padding-top:58px" in html
    assert "max-width:none" in html
    assert "color:var(--ink);background:transparent;box-shadow:none;font-weight:600" in html
    assert ".nav-links a.nav-link.active{color:var(--acc)" not in html
    assert "color:var(--ink-dim);border:0;text-decoration:none" in html


def test_feedback_discovery_source_is_bilingual_and_submitted():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    controller = (ROOT / "locale-controller.js").read_text(encoding="utf-8")

    for value in (
        "linkedin",
        "github",
        "bootdev",
        "recruiting",
        "search",
        "recommendation",
        "other",
    ):
        assert f'<option value="{value}">' in html
    assert "source: source.value" in html
    assert "Wo hast du dieses Portfolio entdeckt?" in controller
    assert "Where did you discover this portfolio?" in controller


def test_admin_always_shows_feedback_source_including_legacy_entries():
    admin = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")

    assert "const sourceLabel = sourceLabels[item.source] || 'not specified'" in admin
    assert 'source · ${esc(sourceLabel)}' in admin
