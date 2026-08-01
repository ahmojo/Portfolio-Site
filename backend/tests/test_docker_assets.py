from pathlib import Path


def test_production_image_includes_root_javascript_assets():
    dockerfile = (
        Path(__file__).parents[1] / "Dockerfile"
    ).read_text(encoding="utf-8")

    assert "COPY *.js ./" in dockerfile

