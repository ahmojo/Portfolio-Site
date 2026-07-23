from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import db


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
            "ip": visitor_hash,
        })

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


if __name__ == "__main__":
    unittest.main()
