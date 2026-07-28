from __future__ import annotations

import unittest

import httpx

from app.open_source import (
    contribution_key,
    fetch_open_source,
    merge_open_source,
    short_description,
    short_title,
    technology_label,
)


class OpenSourceFormattingTests(unittest.TestCase):
    def test_conventional_prefix_is_removed_from_title(self):
        self.assertEqual(
            short_title("fix(parser): restore scopes before fallback"),
            "Restore scopes before fallback",
        )

    def test_summary_is_preferred_over_checklists_and_code(self):
        body = """
## Summary

Fix explicit deserialization of TOML datetimes without changing generic
cross-format conversions.

## Tests

- [x] `cargo test`
"""
        self.assertEqual(
            short_description(body, "fix: preserve datetimes"),
            "Fix explicit deserialization of TOML datetimes without changing generic cross-format conversions.",
        )

    def test_solution_is_used_when_description_only_references_an_issue(self):
        body = """
# Description

Fixes #2183.

## Solution

This change keeps literal paths separate from glob-safe matching paths.
"""
        self.assertEqual(
            short_description(body, "fix: preserve bracketed names"),
            "This change keeps literal paths separate from glob-safe matching paths.",
        )

    def test_technology_uses_language_and_useful_label(self):
        self.assertEqual(
            technology_label(
                {"language": "Rust", "topics": ["serialization"]},
                [{"name": "bug"}, {"name": "status: ready"}],
            ),
            "Rust \u00b7 Bug fix",
        )

    def test_prefixed_metadata_label_is_humanized(self):
        self.assertEqual(
            technology_label(
                {"language": "Rust", "topics": []},
                [{"name": "A:parser"}],
            ),
            "Rust \u00b7 Parser",
        )

    def test_non_technology_topic_is_skipped(self):
        self.assertEqual(
            technology_label(
                {"language": "TypeScript", "topics": ["hacktoberfest", "i18n"]},
                [],
            ),
            "TypeScript \u00b7 I18N",
        )
class OpenSourceMergeTests(unittest.TestCase):
    def test_saved_edits_and_order_win_while_new_prs_are_appended(self):
        live = [
            {"repo": "toml-rs/toml", "pr": 1194, "title": "Generated", "desc": "Generated", "tech": "Rust"},
            {"repo": "nushell/nushell", "pr": 18666, "title": "Generated", "desc": "Generated", "tech": "Rust"},
        ]
        saved = [
            {"repo": "nushell/nushell", "pr": 18666, "title": "Admin title", "desc": "Admin description", "tech": "Rust \u00b7 Parser"},
            {"repo": "example/manual", "pr": 7, "title": "Manual", "desc": "Manual entry", "tech": "Python", "synced": False},
        ]

        result = merge_open_source(live, saved, [])

        self.assertEqual(
            [contribution_key(item) for item in result],
            ["nushell/nushell#18666", "example/manual#7", "toml-rs/toml#1194"],
        )
        self.assertEqual(result[0]["title"], "Admin title")
        self.assertEqual(result[0]["desc"], "Admin description")
        self.assertTrue(result[0]["synced"])
        self.assertFalse(result[1]["synced"])
        self.assertTrue(result[2]["synced"])

    def test_hidden_synced_pr_stays_removed(self):
        live = [{"repo": "nushell/nushell", "pr": 18666, "title": "Generated", "desc": "Generated", "tech": "Rust"}]
        saved = [{**live[0], "synced": True}]

        result = merge_open_source(live, saved, ["NuShell/NuShell#18666"])

        self.assertEqual(result, [])




class OpenSourceGithubTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_filters_repository_owners_case_insensitively(self):
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path == "/search/issues":
                return httpx.Response(
                    200,
                    json={
                        "items": [
                            {
                                "repository_url": "https://api.github.com/repos/toml-rs/toml",
                                "number": 1194,
                                "title": "fix(toml): preserve datetimes",
                                "body": "## Summary\n\nPreserve typed TOML datetimes.",
                                "labels": [{"name": "bug"}],
                                "closed_at": "2026-07-27T00:00:00Z",
                            },
                            {
                                "repository_url": "https://api.github.com/repos/AHMOJO/private-work",
                                "number": 1,
                                "title": "Own repo",
                                "body": "",
                                "labels": [],
                                "closed_at": "2026-07-28T00:00:00Z",
                            },
                            {
                                "repository_url": "https://api.github.com/repos/Momik-jpg/shared",
                                "number": 2,
                                "title": "Excluded repo",
                                "body": "",
                                "labels": [],
                                "closed_at": "2026-07-26T00:00:00Z",
                            },
                        ]
                    },
                )
            if request.url.path == "/repos/toml-rs/toml":
                return httpx.Response(
                    200, json={"language": "Rust", "topics": ["toml"]}
                )
            return httpx.Response(404)

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            result = await fetch_open_source(
                client,
                user="ahmojo",
                excluded_owners=["Momik-jpg"],
            )

        self.assertEqual([item["repo"] for item in result], ["toml-rs/toml"])
        self.assertEqual(result[0]["tech"], "Rust \u00b7 Bug fix")
        query = requests[0].url.params["q"].lower()
        self.assertIn("-user:ahmojo", query)
        self.assertIn("-user:momik-jpg", query)
        self.assertEqual(
            [request.url.path for request in requests].count(
                "/repos/toml-rs/toml"
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
