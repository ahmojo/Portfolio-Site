from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import db, feedback_storage
from app.config import settings
from app.main import create_app
from app.routers.feedback import feedback_rate_limiter


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        self.original_settings = {
            "env": settings.env,
            "session_secret": settings.session_secret,
            "admin_password": settings.admin_password,
            "allowed_origins": settings.allowed_origins,
        }
        db.DB_PATH = Path(self.temp_dir.name) / "portfolio.db"
        settings.env = "development"
        settings.session_secret = "test-feedback-session-secret-with-32-chars"
        settings.admin_password = "test-admin-password"
        settings.allowed_origins = ["http://testserver"]
        feedback_rate_limiter.clear()
        self.client = TestClient(create_app())

    def tearDown(self):
        self.client.close()
        feedback_rate_limiter.clear()
        db.DB_PATH = self.original_db_path
        for name, value in self.original_settings.items():
            setattr(settings, name, value)
        self.temp_dir.cleanup()

    def test_feedback_stores_rating_optional_source_comment_and_timestamp(self):
        positive = self.client.post(
            "/api/feedback",
            json={
                "rating": "positive",
                "source": "linkedin",
                "comment": "<script>alert(1)</script>",
            },
        )
        negative = self.client.post(
            "/api/feedback",
            json={"rating": "negative", "comment": "   "},
        )

        self.assertEqual(positive.status_code, 201, positive.text)
        self.assertEqual(negative.status_code, 201, negative.text)
        with db.get_conn() as conn:
            columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(feedback)")
            }
            rows = conn.execute(
                "SELECT rating, comment, source, created_at FROM feedback ORDER BY id"
            ).fetchall()

        self.assertEqual(
            columns, {"id", "rating", "comment", "source", "created_at"}
        )
        self.assertEqual(rows[0]["rating"], "positive")
        self.assertEqual(rows[0]["source"], "linkedin")
        self.assertEqual(rows[0]["comment"], "<script>alert(1)</script>")
        self.assertEqual(rows[1]["rating"], "negative")
        self.assertEqual(rows[1]["source"], "")
        self.assertEqual(rows[1]["comment"], "")

    def test_invalid_rating_and_too_long_comment_are_rejected(self):
        invalid_rating = self.client.post(
            "/api/feedback", json={"rating": "neutral", "comment": ""}
        )
        too_long = self.client.post(
            "/api/feedback", json={"rating": "positive", "comment": "x" * 1001}
        )
        invalid_source = self.client.post(
            "/api/feedback", json={"rating": "positive", "source": "instagram"}
        )

        self.assertEqual(invalid_rating.status_code, 422)
        self.assertEqual(too_long.status_code, 422)
        self.assertEqual(invalid_source.status_code, 422)

    def test_existing_feedback_table_is_migrated_with_blank_source(self):
        with db.get_conn() as conn:
            conn.execute("DROP TABLE feedback")
            conn.execute(
                """
                CREATE TABLE feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rating TEXT NOT NULL,
                    comment TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            conn.execute(
                "INSERT INTO feedback (rating, comment) VALUES ('positive', 'legacy')"
            )

        feedback_storage.init_feedback_schema()

        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT rating, comment, source FROM feedback"
            ).fetchone()
        self.assertEqual(dict(row), {
            "rating": "positive", "comment": "legacy", "source": ""
        })

    def test_empty_comment_is_valid_and_honeypot_is_not_stored(self):
        honeypot = self.client.post(
            "/api/feedback",
            json={"rating": "positive", "website": "https://spam.example"},
        )
        empty = self.client.post(
            "/api/feedback", json={"rating": "negative", "comment": ""}
        )

        self.assertEqual(honeypot.status_code, 201)
        self.assertEqual(empty.status_code, 201)
        with db.get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM feedback").fetchone()
        self.assertEqual(row["count"], 1)

    def test_cross_origin_submission_is_rejected(self):
        response = self.client.post(
            "/api/feedback",
            headers={"Origin": "https://evil.example"},
            json={"rating": "positive"},
        )
        self.assertEqual(response.status_code, 403)

    def test_storage_failure_returns_service_unavailable(self):
        with patch(
            "app.routers.feedback.feedback_storage.record_feedback",
            side_effect=sqlite3.OperationalError("test storage failure"),
        ):
            response = self.client.post(
                "/api/feedback", json={"rating": "positive"}
            )
        self.assertEqual(response.status_code, 503)

    def test_rate_limit_and_admin_only_summary(self):
        response = self.client.post(
            "/api/feedback",
            json={"rating": "positive", "source": "linkedin"},
        )
        self.assertEqual(response.status_code, 201)
        for _ in range(2):
            response = self.client.post(
                "/api/feedback", json={"rating": "positive"}
            )
            self.assertEqual(response.status_code, 201)
        limited = self.client.post(
            "/api/feedback", json={"rating": "positive"}
        )
        self.assertEqual(limited.status_code, 429)

        public_read = self.client.get("/api/feedback")
        self.assertEqual(public_read.status_code, 401)

        login = self.client.post(
            "/api/auth/login", json={"password": "test-admin-password"}
        )
        self.assertTrue(login.json()["authenticated"])
        summary = self.client.get("/api/feedback")
        self.assertEqual(summary.status_code, 200, summary.text)
        self.assertEqual(summary.headers["cache-control"], "private, no-store")
        self.assertEqual(summary.json()["total"], 3)
        self.assertEqual(summary.json()["positive"], 3)
        self.assertEqual(summary.json()["negative"], 0)
        self.assertTrue(all("source" in item for item in summary.json()["recent"]))
        self.assertEqual(summary.json()["recent"][-1]["source"], "linkedin")


if __name__ == "__main__":
    unittest.main()
