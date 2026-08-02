from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_project_endpoint_prefers_saved_english_copy():
    content = {
        "projects": [
            {
                "slug": "portfolio",
                "title": "Dieses Portfolio",
                "desc": "Deutsch",
                "stack": "Python",
                "content": "Deutsch",
                "badges": [{"label": "Full-Stack", "variant": "py"}],
            }
        ],
        "translations": {
            "en": {
                "projects": [
                    {
                        "slug": "portfolio",
                        "title": "This portfolio",
                        "desc": "English description",
                        "stack": "Python",
                        "content": "English writeup",
                        "badges": [{"label": "Full stack"}],
                    }
                ]
            }
        },
    }

    with patch("app.main.load_content", return_value=content):
        response = TestClient(app).get("/api/project/portfolio?lang=en")

    assert response.status_code == 200
    assert response.json() == {
        "slug": "portfolio",
        "title": "This portfolio",
        "desc": "English description",
        "stack": "Python",
        "content": "English writeup",
        "badges": [{"label": "Full stack", "variant": "py"}],
        "_localized": "en",
    }

def test_project_endpoint_keeps_default_copy_for_other_locales():
    content = {
        "projects": [
            {
                "slug": "portfolio",
                "title": "Dieses Portfolio",
                "desc": "Deutsch",
                "stack": "Python",
                "content": "Deutsch",
                "badges": [],
            }
        ],
        "translations": {"en": {"projects": [{"slug": "portfolio", "title": "This portfolio"}]}},
    }

    with patch("app.main.load_content", return_value=content):
        response = TestClient(app).get("/api/project/portfolio?lang=de")

    assert response.status_code == 200
    assert response.json()["title"] == "Dieses Portfolio"
    assert "_localized" not in response.json()