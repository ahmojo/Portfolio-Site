from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import db
from app.main import _is_likely_human_page_view, create_app


class AnalyticsStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = Path(self.temp_dir.name) / "portfolio.db"
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_new_visit_stores_only_reduced_fields(self):
        visitor_hash = "a" * 32
        db.record_visit("/", "example.com", visitor_hash)

        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT path, referrer, user_agent, ip FROM visits"
            ).fetchone()

        self.assertEqual(dict(row), {
            "path": "/",
            "referrer": "example.com",
            "user_agent": "",
            "ip": f"{db.ANALYTICS_TOKEN_PREFIX}{visitor_hash}",
        })

    def test_repeat_visit_is_counted_once_per_page_and_day(self):
        visitor_hash = "b" * 32
        db.record_visit("/", "", visitor_hash)
        db.record_visit("/", "", visitor_hash)
        db.record_visit("/datenschutz.html", "", visitor_hash)

        result = db.analytics(30)

        self.assertEqual(result["total_visits"], 2)
        self.assertEqual(result["unique_visitors"], 1)

    def test_analytics_excludes_legacy_unclassified_rows_and_honors_window(self):
        with db.get_conn() as conn:
            conn.execute(
                "INSERT INTO visits (path, ip, created_at) VALUES (?, ?, datetime('now'))",
                ("/wp-admin", "c" * 32),
            )
            conn.execute(
                "INSERT INTO visits (path, ip, created_at) "
                "VALUES (?, ?, datetime('now', '-10 days'))",
                ("/", f"{db.ANALYTICS_TOKEN_PREFIX}{'d' * 32}"),
            )
        db.record_visit("/", "", "e" * 32)

        self.assertEqual(db.analytics(7)["total_visits"], 1)
        self.assertEqual(db.analytics(30)["total_visits"], 2)

    def test_old_visits_are_deleted_after_retention_period(self):
        with db.get_conn() as conn:
            conn.execute(
                "INSERT INTO visits (path, ip, created_at) "
                "VALUES (?, ?, datetime('now', '-91 days'))",
                ("/", f"{db.ANALYTICS_TOKEN_PREFIX}{'f' * 32}"),
            )

        db.analytics(365)

        with db.get_conn() as conn:
            count = conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        self.assertEqual(count, 0)

    def test_startup_scrubs_legacy_raw_metadata(self):
        with db.get_conn() as conn:
            conn.execute(
                "INSERT INTO visits (path, referrer, user_agent, ip) "
                "VALUES (?, ?, ?, ?)",
                (
                    "/",
                    "https://example.com/private?q=secret",
                    "Full Browser User Agent",
                    "198.51.100.8",
                ),
            )

        db.init_db()

        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT referrer, user_agent, ip FROM visits"
            ).fetchone()
        self.assertEqual(row["referrer"], "example.com")
        self.assertEqual(row["user_agent"], "")
        self.assertEqual(row["ip"], "")

    def test_browser_navigation_is_accepted_but_bots_and_scanners_are_not(self):
        browser = {
            "method": "GET",
            "path": "/",
            "status_code": 200,
            "accept": "text/html,application/xhtml+xml",
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/138.0.0.0 Safari/537.36"
            ),
            "sec_fetch_dest": "document",
        }
        self.assertTrue(_is_likely_human_page_view(**browser))
        self.assertFalse(
            _is_likely_human_page_view(
                **{**browser, "user_agent": "Googlebot/2.1"}
            )
        )
        self.assertFalse(
            _is_likely_human_page_view(**{**browser, "path": "/wp-admin"})
        )
        self.assertFalse(
            _is_likely_human_page_view(**{**browser, "purpose": "prefetch"})
        )
        self.assertFalse(
            _is_likely_human_page_view(
                **{**browser, "global_privacy_control": "1"}
            )
        )

    def test_only_configured_project_pages_are_accepted(self):
        browser = {
            "method": "GET",
            "status_code": 200,
            "accept": "text/html",
            "user_agent": "Mozilla/5.0 Version/18.0 Safari/605.1.15",
            "project_slugs": {"portfolio"},
        }
        self.assertTrue(
            _is_likely_human_page_view(**browser, path="/p/portfolio")
        )
        self.assertFalse(
            _is_likely_human_page_view(**browser, path="/p/not-a-project")
        )

    def test_middleware_records_browser_once_and_ignores_scanner_path(self):
        headers = {
            "accept": "text/html,application/xhtml+xml",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/138.0.0.0 Safari/537.36"
            ),
            "sec-fetch-dest": "document",
        }
        with patch(
            "app.main.resolve_client_ip", return_value="198.51.100.20"
        ):
            with TestClient(create_app()) as client:
                self.assertEqual(client.get("/", headers=headers).status_code, 200)
                self.assertEqual(client.get("/", headers=headers).status_code, 200)
                self.assertEqual(
                    client.get("/wp-admin", headers=headers).status_code, 200
                )

        result = db.analytics(30)
        self.assertEqual(result["total_visits"], 1)
        self.assertEqual(result["top_paths"], [{"path": "/", "visits": 1}])


if __name__ == "__main__":
    unittest.main()
