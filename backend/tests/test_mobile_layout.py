from pathlib import Path


def test_mobile_uptime_strip_contains_status_without_horizontal_overflow():
    index_html = (Path(__file__).parents[2] / "index.html").read_text(encoding="utf-8")

    assert "html{scroll-behavior:smooth;overflow-x:hidden}" in index_html
    assert (
        ".ops-strip{display:grid;grid-template-columns:minmax(0,1fr) auto;"
        "align-items:center;gap:10px;min-height:72px;padding:12px}"
    ) in index_html
    assert (
        ".ops-title{min-width:0;white-space:normal;"
        "overflow-wrap:anywhere;line-height:1.45}"
    ) in index_html
    assert ".ops-link{width:auto;max-width:100%;justify-self:end}" in index_html
