from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app import analytics_storage, db
from app.analytics_security import TurnstileResult, confirm_rate_limiter
from app.config import settings
from app.main import _is_likely_human_page_view, _security_headers, create_app


PAGE_HEADERS = {
    "accept": "text/html,application/xhtml+xml",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/138.0.0.0 Safari/537.36"
    ),
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
}
CONFIRM_HEADERS = {
    "origin": "http://testserver",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
}


class AnalyticsStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = Path(self.temp_dir.name) / "portfolio.db"
        self.original_settings = {
            "analytics_strict": settings.analytics_strict,
            "analytics_hostname": settings.analytics_hostname,
            "turnstile_site_key": settings.turnstile_site_key,
            "turnstile_secret_key": settings.turnstile_secret_key,
            "session_secret": settings.session_secret,
            "secure_cookies": settings.secure_cookies,
        }
        settings.analytics_strict = True
        settings.analytics_hostname = "testserver"
        settings.turnstile_site_key = "test-site-key"
        settings.turnstile_secret_key = "test-secret-key"
        settings.session_secret = "test-session-secret-with-at-least-32-characters"
        settings.secure_cookies = False
        confirm_rate_limiter.clear()
        db.init_db()
        analytics_storage.init_analytics_schema()

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        for name, value in self.original_settings.items():
            setattr(settings, name, value)
        confirm_rate_limiter.clear()
        self.temp_dir.cleanup()

    def _client(self):
        return TestClient(create_app())

    def _confirm_with_turnstile(
        self, client: TestClient, path: str = "/"
    ):
        first = client.post(
            "/api/analytics/confirm",
            headers=CONFIRM_HEADERS,
            json={"path": path},
        )
        self.assertEqual(first.status_code, 428)
        self.assertEqual(first.json()["detail"], "turnstile_required")
        verifier = AsyncMock(return_value=TurnstileResult(valid=True))
        with patch(
            "app.main.analytics_security.verify_turnstile_token",
            new=verifier,
        ):
            confirmed = client.post(
                "/api/analytics/confirm",
                headers=CONFIRM_HEADERS,
                json={"path": path, "turnstile_token": "valid-token"},
            )
        self.assertEqual(confirmed.status_code, 200, confirmed.text)
        verifier.assert_awaited_once()
        return confirmed

    def test_schema_migration_adds_verification_fields(self):
        with db.get_conn() as conn:
            columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(visits)")
            }
        self.assertIn("verification_method", columns)
        self.assertIn("confidence", columns)

    def test_confirmed_visit_stores_only_reduced_fields_and_provenance(self):
        visitor_hash = "a" * 32
        analytics_storage.record_confirmed_visit(
            "/",
            "example.com",
            visitor_hash,
            verification_method="turnstile",
            confidence=100,
        )

        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT path, referrer, user_agent, ip, "
                "verification_method, confidence FROM visits"
            ).fetchone()

        self.assertEqual(
            dict(row),
            {
                "path": "/",
                "referrer": "example.com",
                "user_agent": "",
                "ip": f"{db.ANALYTICS_TOKEN_PREFIX}{visitor_hash}",
                "verification_method": "turnstile",
                "confidence": 100,
            },
        )

    def test_repeat_confirmed_visit_is_counted_once_per_page_and_day(self):
        visitor_hash = "b" * 32
        analytics_storage.record_confirmed_visit("/", "", visitor_hash)
        analytics_storage.record_confirmed_visit("/", "", visitor_hash)
        analytics_storage.record_confirmed_visit(
            "/datenschutz.html", "", visitor_hash
        )

        result = analytics_storage.analytics(30)

        self.assertEqual(result["confirmed_pageviews"], 2)
        self.assertEqual(result["confirmed_visitor_days"], 1)

    def test_strict_analytics_excludes_legacy_rows(self):
        with db.get_conn() as conn:
            conn.execute(
                "INSERT INTO visits "
                "(path, ip, verification_method, confidence) VALUES (?, ?, ?, ?)",
                (
                    "/impressum.html",
                    f"{db.ANALYTICS_TOKEN_PREFIX}{'c' * 32}",
                    "legacy",
                    0,
                ),
            )
        analytics_storage.record_confirmed_visit("/", "", "d" * 32)

        result = analytics_storage.analytics(30)

        self.assertEqual(result["confirmed_pageviews"], 1)
        self.assertEqual(result["top_paths"], [{"path": "/", "visits": 1}])

    def test_forged_browser_headers_without_fetch_metadata_are_rejected(self):
        forged = {
            "method": "GET",
            "path": "/",
            "status_code": 200,
            "accept": PAGE_HEADERS["accept"],
            "user_agent": PAGE_HEADERS["user-agent"],
        }
        self.assertFalse(_is_likely_human_page_view(**forged))

        with patch(
            "app.main.resolve_client_ip", return_value="198.51.100.20"
        ):
            with self._client() as client:
                response = client.get(
                    "/",
                    headers={
                        "accept": PAGE_HEADERS["accept"],
                        "user-agent": PAGE_HEADERS["user-agent"],
                    },
                )

        self.assertNotIn(settings.analytics_seed_cookie, response.cookies)
        diagnostics = analytics_storage.analytics(30)["diagnostics"]
        self.assertEqual(diagnostics["missing_fetch_metadata"], 1)
        self.assertEqual(diagnostics["confirmed"], 0)

    def test_only_complete_navigation_gets_seed_but_not_immediate_visit(self):
        self.assertTrue(
            _is_likely_human_page_view(
                method="GET",
                path="/",
                status_code=200,
                accept=PAGE_HEADERS["accept"],
                user_agent=PAGE_HEADERS["user-agent"],
                sec_fetch_dest="document",
                sec_fetch_mode="navigate",
                sec_fetch_site="none",
                sec_fetch_user="?1",
            )
        )
        with patch(
            "app.main.resolve_client_ip", return_value="198.51.100.20"
        ):
            with self._client() as client:
                response = client.get("/", headers=PAGE_HEADERS)

        self.assertIn(settings.analytics_seed_cookie, response.cookies)
        self.assertEqual(
            analytics_storage.analytics(30)["confirmed_pageviews"], 0
        )
        self.assertEqual(response.headers["cache-control"], "private, no-store")

    def test_trusted_cloudflare_verified_bot_never_gets_seed(self):
        headers = {**PAGE_HEADERS, "x-portfolio-verified-bot": "true"}
        with (
            patch("app.main._is_trusted_proxy", return_value=True),
            patch(
                "app.main.resolve_client_ip", return_value="198.51.100.21"
            ),
        ):
            with self._client() as client:
                response = client.get("/", headers=headers)

        self.assertNotIn(settings.analytics_seed_cookie, response.cookies)
        self.assertEqual(
            analytics_storage.analytics(30)["diagnostics"]["known_bot"], 1
        )

    def test_spoofed_verified_bot_header_from_untrusted_peer_is_ignored(self):
        headers = {**PAGE_HEADERS, "x-portfolio-verified-bot": "true"}
        with (
            patch("app.main._is_trusted_proxy", return_value=False),
            patch(
                "app.main.resolve_client_ip", return_value="198.51.100.22"
            ),
        ):
            with self._client() as client:
                response = client.get("/", headers=headers)

        self.assertIn(settings.analytics_seed_cookie, response.cookies)

    def test_turnstile_confirmation_is_only_counting_path(self):
        with patch(
            "app.main.resolve_client_ip", return_value="198.51.100.23"
        ):
            with self._client() as client:
                page = client.get("/", headers=PAGE_HEADERS)
                self.assertEqual(page.status_code, 200)
                confirmed = self._confirm_with_turnstile(client)

        self.assertTrue(confirmed.json()["counted"])
        result = analytics_storage.analytics(30)
        self.assertEqual(result["confirmed_pageviews"], 1)
        self.assertEqual(result["recent"][0]["verification_method"], "turnstile")
        self.assertEqual(result["diagnostics"]["confirmed"], 1)

    def test_invalid_turnstile_token_is_rejected(self):
        verifier = AsyncMock(return_value=TurnstileResult(valid=False))
        with (
            patch(
                "app.main.resolve_client_ip", return_value="198.51.100.24"
            ),
            patch(
                "app.main.analytics_security.verify_turnstile_token",
                new=verifier,
            ),
        ):
            with self._client() as client:
                client.get("/", headers=PAGE_HEADERS)
                response = client.post(
                    "/api/analytics/confirm",
                    headers=CONFIRM_HEADERS,
                    json={"path": "/", "turnstile_token": "bad-token"},
                )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            analytics_storage.analytics(30)["diagnostics"]["turnstile_failed"],
            1,
        )
        self.assertEqual(
            analytics_storage.analytics(30)["confirmed_pageviews"], 0
        )

    def test_seed_is_bound_to_original_path(self):
        with patch(
            "app.main.resolve_client_ip", return_value="198.51.100.25"
        ):
            with self._client() as client:
                client.get("/", headers=PAGE_HEADERS)
                response = client.post(
                    "/api/analytics/confirm",
                    headers=CONFIRM_HEADERS,
                    json={"path": "/impressum.html"},
                )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "invalid_seed")

    def test_seed_replay_is_rejected(self):
        verifier = AsyncMock(return_value=TurnstileResult(valid=True))
        with (
            patch(
                "app.main.resolve_client_ip", return_value="198.51.100.26"
            ),
            patch(
                "app.main.analytics_security.verify_turnstile_token",
                new=verifier,
            ),
        ):
            with self._client() as client:
                page = client.get("/", headers=PAGE_HEADERS)
                seed = page.cookies.get(settings.analytics_seed_cookie)
                first = client.post(
                    "/api/analytics/confirm",
                    headers=CONFIRM_HEADERS,
                    json={"path": "/", "turnstile_token": "token-one"},
                )
                client.cookies.set(
                    settings.analytics_seed_cookie,
                    seed,
                    path="/api/analytics/confirm",
                )
                second = client.post(
                    "/api/analytics/confirm",
                    headers=CONFIRM_HEADERS,
                    json={"path": "/", "turnstile_token": "token-two"},
                )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["detail"], "seed_replayed")

    def test_daily_human_cookie_avoids_second_turnstile_challenge(self):
        with patch(
            "app.main.resolve_client_ip", return_value="198.51.100.27"
        ):
            with self._client() as client:
                client.get("/", headers=PAGE_HEADERS)
                self._confirm_with_turnstile(client)
                second_headers = {**PAGE_HEADERS, "sec-fetch-site": "same-origin"}
                client.get("/datenschutz.html", headers=second_headers)
                second = client.post(
                    "/api/analytics/confirm",
                    headers=CONFIRM_HEADERS,
                    json={"path": "/datenschutz.html"},
                )

        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(
            analytics_storage.analytics(30)["confirmed_pageviews"], 2
        )

    def test_wrong_origin_and_fetch_context_are_rejected(self):
        with patch(
            "app.main.resolve_client_ip", return_value="198.51.100.28"
        ):
            with self._client() as client:
                client.get("/", headers=PAGE_HEADERS)
                wrong_origin = client.post(
                    "/api/analytics/confirm",
                    headers={**CONFIRM_HEADERS, "origin": "https://evil.example"},
                    json={"path": "/"},
                )
                wrong_fetch = client.post(
                    "/api/analytics/confirm",
                    headers={
                        **CONFIRM_HEADERS,
                        "sec-fetch-mode": "navigate",
                    },
                    json={"path": "/"},
                )

        self.assertEqual(wrong_origin.status_code, 403)
        self.assertEqual(wrong_fetch.status_code, 403)

    def test_public_pages_receive_shared_client_script_and_csp_allows_turnstile(self):
        with patch(
            "app.main.resolve_client_ip", return_value="198.51.100.29"
        ):
            with self._client() as client:
                for path in (
                    "/",
                    "/impressum.html",
                    "/datenschutz.html",
                    "/p/portfolio",
                ):
                    response = client.get(path, headers=PAGE_HEADERS)
                    self.assertIn(
                        '<script src="/api/analytics/client.js" defer></script>',
                        response.text,
                    )

        csp = _security_headers()["Content-Security-Policy"]
        self.assertIn(
            "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com",
            csp,
        )
        self.assertIn("frame-src https://challenges.cloudflare.com", csp)


if __name__ == "__main__":
    unittest.main()
