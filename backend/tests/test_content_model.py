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


if __name__ == "__main__":
    unittest.main()
