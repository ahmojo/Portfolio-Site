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

    assert "filter(def => hasMetric(p[def.key]))" in html
    assert 'aria-hidden="true">${def.icon}' in html
    assert 'class="cct-metrics-help"' in html
    assert 'type="button"' in html
    assert '<dialog class="cct-help-dialog"' in html
    assert "dialog.showModal()" in html
    assert "metricPoints(p, def.key)" in html


def test_metric_copy_preserves_required_semantics():
    locale = (ROOT / "locale.js").read_text(encoding="utf-8")

    assert "Eindeutige Klon-Quellen · 14 Tage" in locale
    assert "Unique clone sources · 14 days" in locale
    assert "automatisierte Zugriffe durch CI" in locale
    assert "automated access from CI systems" in locale
    assert "rollierende 14-Tage-Fenster" in locale
    assert "rolling 14-day window" in locale
    assert "all-time unique" not in locale.lower()
    assert "Lifetime Unique Users" not in locale


def test_mobile_help_is_a_viewport_bound_bottom_sheet():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert ".cct-help-dialog::backdrop" in html
    assert "inset:auto 0 0;width:100vw;max-width:100vw" in html
    assert "safe-area-inset-bottom" in html


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
