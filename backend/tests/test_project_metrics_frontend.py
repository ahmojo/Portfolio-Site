from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[2]


def test_partial_metrics_are_guarded_before_rendering():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    for field in (
        "release_downloads",
        "unique_cloners_14d",
        "tracked_total_clones",
        "clones_14d",
    ):
        assert f"key:'{field}'" in html

    assert "window.__cctMetricVisibility?.[def.key] !== false" in html
    assert 'aria-hidden="true">${def.icon}' in html
    assert 'class="cct-metrics-help"' in html
    assert 'type="button"' in html
    assert 'class="cct-help-layer"' in html
    assert 'class="cct-help-panel" role="dialog"' in html
    assert "helpLayer.hidden=false" in html
    assert "metricPoints(p, def.key)" in html


def test_metric_copy_preserves_required_semantics():
    locale = (ROOT / "locale.js").read_text(encoding="utf-8")

    assert "Eindeutige Klon-Quellen in den letzten 14 Tagen" in locale
    assert "Unique clone sources in the last 14 days" in locale
    assert "automatisierte Zugriffe durch CI" in locale
    assert "automated access from CI systems" in locale
    assert "rollierend" not in locale
    assert "rolling window" not in locale
    assert "all-time unique" not in locale.lower()
    assert "Lifetime Unique Users" not in locale


def test_mobile_help_is_a_viewport_bound_bottom_sheet():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert ".cct-help-layer{position:fixed;inset:0" in html
    assert ".cct-help-backdrop{display:block;position:absolute;inset:0" in html
    assert "width:100%;max-width:none" in html
    assert "safe-area-inset-bottom" in html


def test_desktop_help_is_anchored_and_metric_grid_handles_hidden_cards():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert ".cct-help-layer{position:absolute;z-index:18;right:0;top:39px}" in html
    assert '.cct-metrics-grid[data-count="1"]' in html
    assert 'data-count="${defs.length}"' in html


def test_locale_switch_rerenders_metrics_without_refetching_content():
    controller = (ROOT / "locale-controller.js").read_text(encoding="utf-8")
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "window.__rerenderProjectMeta" in controller
    assert "window.__rerenderProjectMeta = () =>" in html


def test_project_writeup_link_carries_the_selected_language():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "window.__portfolioLocale === 'en' ? '?lang=en' : ''" in html
    assert "window.__portfolioLocale === 'en' ? 'read more' : 'mehr lesen'" in html
    assert '`<a href="/p/${esc(p.slug)}${projectLocale}"' in html


def test_admin_can_hide_each_metric_and_chart_opens_are_aggregated():
    admin = (ROOT / "admin" / "admin.html").read_text(encoding="utf-8")
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    for field in (
        "release_downloads",
        "tracked_total_clones",
        "unique_cloners_14d",
        "clones_14d",
    ):
        assert f'data-cct-metric="{field}"' in admin
    assert "/api/analytics/metric-open" in html
    assert "Metric chart opens" in admin


def test_inline_frontend_scripts_have_valid_javascript():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed")

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    inline_scripts = re.findall(
        r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert inline_scripts
    for script in inline_scripts:
        result = subprocess.run(
            [node, "--check", "-"],
            input=script,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
