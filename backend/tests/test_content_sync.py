from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi import Response

from app.routers.content import get_content


class ContentSyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_content_endpoint_returns_admin_overrides_plus_new_prs(self):
        saved = {
            "open_source": [
                {
                    "repo": "nushell/nushell",
                    "pr": 18666,
                    "title": "Admin title",
                    "desc": "Admin description",
                    "tech": "Rust \u00b7 Parser",
                }
            ]
        }
        live = [
            {
                "repo": "nushell/nushell",
                "pr": 18666,
                "title": "Generated title",
                "desc": "Generated description",
                "tech": "Rust",
                "synced": True,
            },
            {
                "repo": "toml-rs/toml",
                "pr": 1194,
                "title": "New contribution",
                "desc": "Automatically discovered",
                "tech": "Rust \u00b7 TOML",
                "synced": True,
            },
        ]

        with (
            patch("app.routers.content.load_content", return_value=saved),
            patch(
                "app.routers.content.get_open_source",
                new=AsyncMock(return_value=live),
            ),
        ):
            result = await get_content(Response())

        self.assertEqual(len(result.open_source), 2)
        self.assertEqual(result.open_source[0].title, "Admin title")
        self.assertEqual(result.open_source[0].desc, "Admin description")
        self.assertTrue(result.open_source[0].synced)
        self.assertEqual(result.open_source[1].repo, "toml-rs/toml")


if __name__ == "__main__":
    unittest.main()
