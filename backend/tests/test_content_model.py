from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.models import SiteContent


class SiteContentOpenSourceTests(unittest.TestCase):
    def test_legacy_content_gets_default_open_source_items(self):
        content = SiteContent.model_validate({})

        self.assertEqual(
            [item.repo for item in content.open_source],
            [
                "nushell/nushell",
                "pygments/pygments",
                "go-git/go-git",
                "lingui/js-lingui",
                "toml-rs/toml",
            ],
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

    def test_english_translation_copy_is_preserved(self):
        content = SiteContent.model_validate(
            {
                "translations": {
                    "en": {
                        "hero": {"lede": "English hero"},
                        "projects": [
                            {
                                "slug": "portfolio",
                                "title": "This portfolio",
                                "desc": "English description",
                            }
                        ],
                    }
                }
            }
        )

        self.assertEqual(content.translations["en"].hero.lede, "English hero")
        self.assertEqual(content.translations["en"].projects[0].title, "This portfolio")

    def test_only_english_translation_key_is_accepted(self):
        with self.assertRaises(ValidationError):
            SiteContent.model_validate({"translations": {"fr": {}}})

    def test_legacy_content_shows_all_cct_metrics_by_default(self):
        content = SiteContent.model_validate({})

        self.assertTrue(content.cct_metrics.release_downloads)
        self.assertTrue(content.cct_metrics.tracked_total_clones)
        self.assertTrue(content.cct_metrics.unique_cloners_14d)
        self.assertTrue(content.cct_metrics.clones_14d)

    def test_cct_metric_visibility_is_preserved(self):
        content = SiteContent.model_validate(
            {"cct_metrics": {"unique_cloners_14d": False}}
        )

        self.assertFalse(content.cct_metrics.unique_cloners_14d)
        self.assertTrue(content.cct_metrics.release_downloads)
if __name__ == "__main__":
    unittest.main()
