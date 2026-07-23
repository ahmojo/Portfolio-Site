from __future__ import annotations

import unittest
from datetime import date

from app.privacy import daily_visitor_hash, referrer_hostname, resolve_client_ip


class PrivacyTests(unittest.TestCase):
    def test_untrusted_peer_cannot_spoof_forwarded_headers(self):
        resolved = resolve_client_ip(
            "203.0.113.8",
            "198.51.100.77",
            "198.51.100.88",
            ["173.245.48.0/20"],
        )
        self.assertEqual(resolved, "203.0.113.8")

    def test_trusted_peer_can_supply_cloudflare_client_ip(self):
        resolved = resolve_client_ip(
            "173.245.48.10",
            "198.51.100.77",
            "198.51.100.88",
            ["173.245.48.0/20"],
        )
        self.assertEqual(resolved, "198.51.100.77")

    def test_referrer_keeps_only_hostname(self):
        self.assertEqual(
            referrer_hostname("https://Example.COM/private/path?q=secret#part"),
            "example.com",
        )
        self.assertEqual(referrer_hostname("javascript:alert(1)"), "")

    def test_daily_hash_is_stable_for_one_day_and_rotates(self):
        first = daily_visitor_hash(
            "198.51.100.10", "test-secret", date(2026, 7, 23)
        )
        same = daily_visitor_hash(
            "198.51.100.10", "test-secret", date(2026, 7, 23)
        )
        next_day = daily_visitor_hash(
            "198.51.100.10", "test-secret", date(2026, 7, 24)
        )
        self.assertEqual(first, same)
        self.assertNotEqual(first, next_day)
        self.assertNotIn("198.51.100.10", first)


if __name__ == "__main__":
    unittest.main()
