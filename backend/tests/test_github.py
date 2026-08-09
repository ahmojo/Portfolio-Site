from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import github
from app.github import (
    fetch_release_downloads,
    fetch_repo,
    fetch_cct_usage,
    fetch_traffic_metrics,
    get_projects,
)
from app.models import ProjectOut
from app.routers import projects as projects_router


def release(*assets, draft=False):
    return {
        "draft": draft,
        "assets": [
            {"name": name, "download_count": count} for name, count in assets
        ],
    }


class GithubMetadataTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        github._cache.clear()
        github._cache_ts.clear()
        github._usage_cache.clear()
        github._usage_attempt_ts.clear()

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

    async def test_counts_current_cct_binaries(self):
        payload = [
            release(
                ("cct_v1.8.0_windows_amd64.tar.gz", 4),
                ("cct_v1.8.0_darwin_arm64.tar.gz", 7),
                ("cct_v1.8.0_linux_arm64.zip", 3),
            )
        ]

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=payload)
            )
        ) as client:
            self.assertEqual(await fetch_release_downloads(client), 14)

    async def test_counts_historical_codex_sync_binaries(self):
        payload = [
            release(
                ("codex-sync_v0.1.13_linux_amd64.tar.gz", 11),
                ("codex-sync_v0.1.13_darwin_arm64.tar.gz", 5),
            )
        ]

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=payload)
            )
        ) as client:
            self.assertEqual(await fetch_release_downloads(client), 16)

    async def test_excludes_non_installable_release_assets_and_drafts(self):
        payload = [
            release(
                ("SHA256SUMS.txt", 100),
                ("SHA256SUMS.txt.sigstore.json", 100),
                ("cct_v1.8.0_sbom.spdx.json", 100),
                ("codex-claude-transfer-1.8.0-deps.tar.xz", 100),
                ("cct_v1.8.0_linux_386.tar.gz", 100),
                ("cct_v1.8.0_linux_amd64.tar.gz", 2),
            ),
            release(("cct_v1.9.0_linux_amd64.tar.gz", 50), draft=True),
        ]

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=payload)
            )
        ) as client:
            self.assertEqual(await fetch_release_downloads(client), 2)

    async def test_release_fetch_paginates_after_100_releases(self):
        requested_pages = []

        def handler(request: httpx.Request) -> httpx.Response:
            page = int(request.url.params["page"])
            requested_pages.append(page)
            if page == 1:
                return httpx.Response(200, json=[release()] * 100)
            return httpx.Response(
                200,
                json=[release(("cct_v2.0.0_linux_amd64.tar.gz", 9))],
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            self.assertEqual(await fetch_release_downloads(client), 9)

        self.assertEqual(requested_pages, [1, 2])

    async def test_release_fetch_returns_none_on_error(self):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(503)
            )
        ) as client:
            self.assertIsNone(await fetch_release_downloads(client))

    async def test_fetches_public_traffic_metrics(self):
        payload = {
            "schema_version": 1,
            "repo": github._CCT_REPO,
            "tracked_since": "2026-08-01",
            "updated_at": "2026-08-07T03:17:00Z",
            "clones_14d": 12,
            "unique_cloners_14d": 7,
            "tracked_total_clones": 18,
            "days": {},
        }
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=payload)
            )
        ) as client:
            result = await fetch_traffic_metrics(client)

        self.assertEqual(
            result,
            {
                "clones_14d": 12,
                "unique_cloners_14d": 7,
                "tracked_total_clones": 18,
                "tracked_since": "2026-08-01",
                "metrics_updated_at": "2026-08-07T03:17:00Z",
            },
        )

    async def test_traffic_metrics_return_none_on_http_error(self):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(503)
            )
        ) as client:
            self.assertIsNone(await fetch_traffic_metrics(client))

    async def test_fetches_chronological_metric_snapshots(self):
        payload = {
            "schema_version": 1,
            "repo": github._CCT_REPO,
            "tracked_since": "2026-08-01",
            "updated_at": "2026-08-08T03:17:00Z",
            "release_downloads": 25,
            "clones_14d": 12,
            "unique_cloners_14d": 7,
            "tracked_total_clones": 18,
            "days": {},
            "snapshots": {
                "invalid": {"release_downloads": 999},
                "2026-08-08": {
                    "release_downloads": 25,
                    "clones_14d": 12,
                },
                "2026-08-07": {
                    "release_downloads": 20,
                    "clones_14d": 9,
                },
            },
        }
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=payload)
            )
        ) as client:
            result = await fetch_traffic_metrics(client)

        self.assertEqual(result["release_downloads"], 25)
        self.assertEqual(
            result["metrics_history"],
            [
                {
                    "date": "2026-08-07",
                    "release_downloads": 20,
                    "clones_14d": 9,
                },
                {
                    "date": "2026-08-08",
                    "release_downloads": 25,
                    "clones_14d": 12,
                },
            ],
        )

    async def test_usage_deltas_compare_with_previous_daily_snapshot(self):
        traffic = {
            "clones_14d": 12,
            "unique_cloners_14d": 7,
            "tracked_total_clones": 18,
            "metrics_history": [
                {
                    "date": "2026-08-07",
                    "release_downloads": 20,
                    "clones_14d": 9,
                    "unique_cloners_14d": 6,
                    "tracked_total_clones": 13,
                },
                {
                    "date": "2026-08-08",
                    "release_downloads": 23,
                    "clones_14d": 12,
                    "unique_cloners_14d": 7,
                    "tracked_total_clones": 18,
                },
            ],
        }
        with (
            patch(
                "app.github.fetch_release_downloads",
                new=AsyncMock(return_value=25),
            ),
            patch(
                "app.github.fetch_traffic_metrics",
                new=AsyncMock(return_value=traffic),
            ),
        ):
            result = await fetch_cct_usage(AsyncMock())

        self.assertEqual(result["release_downloads_delta_1d"], 5)
        self.assertEqual(result["clones_14d_delta_1d"], 3)
        self.assertEqual(result["unique_cloners_14d_delta_1d"], 1)
        self.assertEqual(result["tracked_total_clones_delta_1d"], 5)
    async def test_project_output_keeps_cached_usage_after_refresh_failure(self):
        github._usage_cache[github._CCT_REPO] = {
            "release_downloads": 23,
            "tracked_total_clones": 41,
        }
        repo_data = {
            "repo": github._CCT_REPO,
            "url": f"https://github.com/{github._CCT_REPO}",
            "stars": 1,
            "forks": 0,
            "language": "Go",
            "updated_at": None,
            "description": None,
            "exists": True,
        }
        with (
            patch("app.github.fetch_repo", new=AsyncMock(return_value=repo_data)),
            patch("app.github.fetch_cct_usage", new=AsyncMock(return_value={})),
        ):
            result = await get_projects([("CCT", github._CCT_REPO)])

        self.assertEqual(result[0]["release_downloads"], 23)
        self.assertEqual(result[0]["tracked_total_clones"], 41)

    async def test_project_output_uses_null_for_unknown_usage(self):
        repo_data = {
            "repo": github._CCT_REPO,
            "url": f"https://github.com/{github._CCT_REPO}",
            "stars": 1,
            "forks": 0,
            "language": "Go",
            "updated_at": None,
            "description": None,
            "exists": True,
        }
        with (
            patch("app.github.fetch_repo", new=AsyncMock(return_value=repo_data)),
            patch("app.github.fetch_cct_usage", new=AsyncMock(return_value={})),
        ):
            result = await get_projects([("CCT", github._CCT_REPO)])

        self.assertIsNone(result[0]["release_downloads"])
        self.assertIsNone(result[0]["unique_cloners_14d"])
        self.assertIsNone(result[0]["tracked_total_clones"])

    def test_projects_api_serializes_unavailable_metrics_as_null(self):
        api = FastAPI()
        api.include_router(projects_router.router)
        project = {
            "name": "Example",
            "repo": "ahmojo/example",
            "url": "https://github.com/ahmojo/example",
            "stars": 0,
            "forks": 0,
        }
        with (
            patch(
                "app.routers.projects.load_content",
                return_value={"projects": [{"title": "Example", "repo": "ahmojo/example"}]},
            ),
            patch(
                "app.routers.projects.get_projects",
                new=AsyncMock(return_value=[project]),
            ),
            TestClient(api) as client,
        ):
            response = client.get("/api/projects")

        self.assertEqual(response.status_code, 200)
        payload = response.json()[0]
        self.assertIsNone(payload["release_downloads"])
        self.assertIsNone(payload["clones_14d"])
        self.assertIsNone(payload["unique_cloners_14d"])
        self.assertIsNone(payload["tracked_total_clones"])
        self.assertIsNone(payload["release_downloads_delta_1d"])
        self.assertIsNone(payload["metrics_history"])
    def test_response_model_keeps_fork_count(self):
        project = ProjectOut(
            name="Example",
            repo="ahmojo/example",
            url="https://github.com/ahmojo/example",
            stars=3,
            forks=2,
        )
        self.assertEqual(project.model_dump()["forks"], 2)

    def test_response_model_defaults_usage_to_null(self):
        project = ProjectOut(
            name="Example",
            repo="ahmojo/example",
            url="https://github.com/ahmojo/example",
            stars=0,
        )
        output = project.model_dump()
        self.assertIsNone(output["release_downloads"])
        self.assertIsNone(output["tracked_total_clones"])
        self.assertIsNone(output["release_downloads_delta_1d"])
        self.assertIsNone(output["metrics_history"])


if __name__ == "__main__":
    unittest.main()
