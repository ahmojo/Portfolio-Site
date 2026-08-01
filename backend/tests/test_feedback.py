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

    def test_positive_and_negative_feedback_store_only_required_fields(self):
        positive = self.client.post(
            "/api/feedback",
            json={
                "rating": "positive",
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
                "SELECT rating, comment, created_at FROM feedback ORDER BY id"
            ).fetchall()

        self.assertEqual(columns, {"id", "rating", "comment", "created_at"})
        self.assertEqual(rows[0]["rating"], "positive")
        self.assertEqual(rows[0]["comment"], "<script>alert(1)</script>")
        self.assertEqual(rows[1]["rating"], "negative")
        self.assertEqual(rows[1]["comment"], "")

    def test_invalid_rating_and_too_long_comment_are_rejected(self):
        invalid_rating = self.client.post(
            "/api/feedback", json={"rating": "neutral", "comment": ""}
        )
        too_long = self.client.post(
            "/api/feedback", json={"rating": "positive", "comment": "x" * 1001}
        )

        self.assertEqual(invalid_rating.status_code, 422)
        self.assertEqual(too_long.status_code, 422)

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
        for _ in range(3):
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


if __name__ == "__main__":
    unittest.main()
