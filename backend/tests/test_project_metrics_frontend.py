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
        assert f"hasMetric(p.{field})" in html

    assert "p.tracked_total_clones) && since" in html
    assert 'aria-hidden="true">${icon}' in html
    assert 'class="cct-metrics-help"' in html
    assert 'type="button"' in html


def test_metric_copy_preserves_required_semantics():
    locale = (ROOT / "locale.js").read_text(encoding="utf-8")

    assert "eindeutige Klon-Quellen · 14 Tage" in locale
    assert "unique clone sources · 14 days" in locale
    assert "automatisierte Zugriffe durch CI" in locale
    assert "automated access from CI systems" in locale
    assert "all-time unique" not in locale.lower()
    assert "Lifetime Unique Users" not in locale


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
