from __future__ import annotations

import unittest

import httpx

from app.github import fetch_repo
from app.models import ProjectOut


class GithubMetadataTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_repo_includes_fork_count(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "html_url": "https://github.com/ahmojo/example",
                    "stargazers_count": 3,
                    "forks_count": 2,
                    "language": "Python",
                    "updated_at": "2026-07-23T00:00:00Z",
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            result = await fetch_repo(client, "ahmojo/example")

        self.assertEqual(result["stars"], 3)
        self.assertEqual(result["forks"], 2)

    def test_response_model_keeps_fork_count(self):
        project = ProjectOut(
            name="Example",
            repo="ahmojo/example",
            url="https://github.com/ahmojo/example",
            stars=3,
            forks=2,
        )
        self.assertEqual(project.model_dump()["forks"], 2)


if __name__ == "__main__":
    unittest.main()
