from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

from app import db


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.original_db_path = db.DB_PATH
        db.DB_PATH = self.root / "portfolio.db"
        db.init_db()
        with db.get_conn() as conn:
            conn.execute(
                "UPDATE now_state SET status = 'active-before-restore' WHERE id = 1"
            )

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def _candidate(self, name: str = "candidate.db") -> Path:
        path = self.root / name
        original = db.DB_PATH
        db.DB_PATH = path
        try:
            db.init_db()
            with db.get_conn() as conn:
                conn.execute(
                    "UPDATE now_state SET status = 'restored-content' WHERE id = 1"
                )
        finally:
            db.DB_PATH = original
        return path

    def _active_status(self) -> str:
        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT status FROM now_state WHERE id = 1"
            ).fetchone()
        return row["status"]

    def test_valid_database_is_replaced_and_backup_is_kept(self):
        candidate = self._candidate()

        restored_bytes, backup_path = db.restore_database(candidate)

        self.assertGreater(restored_bytes, 0)
        self.assertEqual(self._active_status(), "restored-content")
        self.assertTrue(backup_path.is_file())
        with closing(sqlite3.connect(backup_path)) as conn:
            old_status = conn.execute(
                "SELECT status FROM now_state WHERE id = 1"
            ).fetchone()[0]
        self.assertEqual(old_status, "active-before-restore")

    def test_header_only_fake_is_rejected_without_changing_active_db(self):
        candidate = self.root / "fake.db"
        candidate.write_bytes(b"SQLite format 3\0" + b"not-a-database")

        with self.assertRaises(db.RestoreValidationError):
            db.restore_database(candidate)

        self.assertEqual(self._active_status(), "active-before-restore")

    def test_database_with_unexpected_schema_is_rejected(self):
        candidate = self.root / "wrong-schema.db"
        with closing(sqlite3.connect(candidate)) as conn:
            conn.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
            conn.commit()

        with self.assertRaises(db.RestoreValidationError):
            db.restore_database(candidate)

        self.assertEqual(self._active_status(), "active-before-restore")

    def test_invalid_site_json_is_rejected(self):
        candidate = self._candidate()
        with closing(sqlite3.connect(candidate)) as conn:
            conn.execute(
                "UPDATE content SET data = ? WHERE key = 'site'",
                ("not-json",),
            )
            conn.commit()

        with self.assertRaises(db.RestoreValidationError):
            db.restore_database(candidate)

        self.assertEqual(self._active_status(), "active-before-restore")

    def test_post_swap_failure_rolls_back_active_database(self):
        candidate = self._candidate()
        real_validate = db.validate_restore_candidate
        calls = 0

        def fail_second_validation(path: Path):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise db.RestoreValidationError("post-swap test failed")
            return real_validate(path)

        with mock.patch.object(
            db, "validate_restore_candidate", side_effect=fail_second_validation
        ):
            with self.assertRaises(db.RestoreValidationError):
                db.restore_database(candidate)

        self.assertEqual(self._active_status(), "active-before-restore")
        db.validate_restore_candidate(db.DB_PATH)


if __name__ == "__main__":
    unittest.main()
