from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.restore_upload import RestoreUploadTooLarge, stage_restore_upload


class FakeUpload:
    def __init__(self, data: bytes):
        self.data = data
        self.read_once = False

    async def read(self, size: int = -1) -> bytes:
        if self.read_once:
            return b""
        self.read_once = True
        return self.data


class RestoreUploadTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_over_limit_is_rejected_and_temp_file_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            with self.assertRaises(RestoreUploadTooLarge):
                await stage_restore_upload(FakeUpload(b"123456"), directory, 5)
            self.assertEqual(list(directory.iterdir()), [])

    async def test_upload_is_staged_on_disk(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            path, size = await stage_restore_upload(
                FakeUpload(b"SQLite bytes"), directory, 100
            )
            self.assertEqual(size, 12)
            self.assertEqual(path.read_bytes(), b"SQLite bytes")


if __name__ == "__main__":
    unittest.main()
