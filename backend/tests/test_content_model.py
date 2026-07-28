from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.models import SiteContent


class SiteContentOpenSourceTests(unittest.TestCase):
    def test_legacy_content_gets_default_open_source_items(self):
        content = SiteContent.model_validate({})

        self.assertEqual(
            [item.repo for item in content.open_source],
            ["nushell/nushell", "pygments/pygments", "go-git/go-git"],
        )

    def test_custom_fourth_item_is_preserved_for_next_grid_row(self):
        content = SiteContent.model_validate(
            {
                "open_source": [
                    {
                        "repo": f"example/repo-{index}",
                        "pr": index,
                        "title": f"Contribution {index}",
                        "desc": "Short description.",
                        "tech": "Python",
                    }
                    for index in range(1, 5)
                ]
            }
        )

        self.assertEqual(len(content.open_source), 4)
        self.assertEqual(content.open_source[-1].repo, "example/repo-4")

    def test_pull_request_number_must_be_positive(self):
        with self.assertRaises(ValidationError):
            SiteContent.model_validate(
                {
                    "open_source": [
                        {
                            "repo": "example/repo",
                            "pr": 0,
                            "title": "Invalid",
                        }
                    ]
                }
            )

    def test_sync_metadata_and_hidden_keys_are_preserved(self):
        content = SiteContent.model_validate(
            {
                "open_source": [
                    {
                        "repo": "example/repo",
                        "pr": 42,
                        "title": "Editable",
                        "synced": True,
                    }
                ],
                "open_source_hidden": ["example/hidden#7"],
            }
        )

        self.assertTrue(content.open_source[0].synced)
        self.assertEqual(content.open_source_hidden, ["example/hidden#7"])


if __name__ == "__main__":
    unittest.main()
