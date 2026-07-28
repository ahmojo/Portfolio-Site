from pathlib import Path


def test_mobile_uptime_strip_stacks_without_horizontal_overflow():
    index_html = (Path(__file__).parents[2] / "index.html").read_text(encoding="utf-8")

    assert ".ops-strip{flex-direction:column;align-items:stretch}" in index_html
    assert ".ops-title{white-space:normal;overflow-wrap:anywhere}" in index_html
    assert ".ops-link{width:max-content;max-width:100%}" in index_html
