"""SQLite persistence for confirmed analytics and anonymous diagnostics."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from . import db
from .config import settings

ANALYTICS_RETENTION_DAYS = 90
ANALYTICS_TOKEN_PREFIX = db.ANALYTICS_TOKEN_PREFIX
_METHODS = {"turnstile", "cloudflare_high_score", "engaged_browser", "legacy"}
_COUNTER_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def init_analytics_schema() -> None:
    """Add analytics columns and tables without invalidating legacy backups."""
    with db.get_conn() as conn:
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(visits)")
        }
        if "verification_method" not in columns:
            conn.execute(
                "ALTER TABLE visits ADD COLUMN "
                "verification_method TEXT NOT NULL DEFAULT 'legacy'"
            )
        if "confidence" not in columns:
            conn.execute(
                "ALTER TABLE visits ADD COLUMN "
                "confidence INTEGER NOT NULL DEFAULT 0"
            )
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS analytics_counters (
                day    TEXT NOT NULL DEFAULT (DATE('now')),
                reason TEXT NOT NULL,
                count  INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (day, reason)
            );
            CREATE TABLE IF NOT EXISTS analytics_confirmed_nonces (
                nonce_hash TEXT PRIMARY KEY,
                expires_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_visits_verification_created
                ON visits(verification_method, created_at);
            """
        )


def _prune(conn) -> None:
    conn.execute(
        "DELETE FROM visits WHERE created_at < datetime('now', ?)",
        (f"-{ANALYTICS_RETENTION_DAYS} days",),
    )
    conn.execute(
        "DELETE FROM analytics_counters WHERE day < DATE('now', ?)",
        (f"-{ANALYTICS_RETENTION_DAYS} days",),
    )
    conn.execute(
        "DELETE FROM analytics_confirmed_nonces WHERE expires_at <= ?",
        (int(datetime.now(timezone.utc).timestamp()),),
    )


def increment_counter(reason: str, amount: int = 1) -> None:
    """Increment one anonymous daily diagnostic counter."""
    if not _COUNTER_NAME.fullmatch(reason) or amount < 1:
        return
    try:
        with db.get_conn() as conn:
            conn.execute(
                "INSERT INTO analytics_counters (day, reason, count) "
                "VALUES (DATE('now'), ?, ?) "
                "ON CONFLICT(day, reason) DO UPDATE "
                "SET count = count + excluded.count",
                (reason, amount),
            )
    except Exception:
        pass


def consume_nonce(nonce: str, expires_at: int) -> bool:
    """Atomically accept a signed seed nonce once."""
    if not nonce:
        return False
    nonce_hash = hashlib.sha256(nonce.encode()).hexdigest()
    try:
        with db.get_conn() as conn:
            _prune(conn)
            cursor = conn.execute(
                "INSERT OR IGNORE INTO analytics_confirmed_nonces "
                "(nonce_hash, expires_at) VALUES (?, ?)",
                (nonce_hash, expires_at),
            )
            return cursor.rowcount == 1
    except Exception:
        return False


def record_confirmed_visit(
    path: str,
    referrer_host: str,
    visitor_hash: str,
    *,
    verification_method: str = "turnstile",
    confidence: int = 100,
) -> bool:
    """Store one verified pageview per path and visitor-day."""
    if not visitor_hash or verification_method not in _METHODS:
        return False
    visitor_token = f"{ANALYTICS_TOKEN_PREFIX}{visitor_hash}"
    safe_path = path[:255] or "/"
    safe_confidence = max(0, min(int(confidence), 100))
    try:
        with db.get_conn() as conn:
            _prune(conn)
            existing = conn.execute(
                "SELECT id, verification_method FROM visits "
                "WHERE path = ? AND ip = ? AND DATE(created_at) = DATE('now') "
                "ORDER BY id DESC LIMIT 1",
                (safe_path, visitor_token),
            ).fetchone()
            if existing:
                if (
                    verification_method == "turnstile"
                    and existing["verification_method"] != "turnstile"
                ):
                    conn.execute(
                        "UPDATE visits SET verification_method = ?, confidence = ?, "
                        "referrer = ?, user_agent = '' WHERE id = ?",
                        (
                            verification_method,
                            safe_confidence,
                            (referrer_host or "")[:255],
                            existing["id"],
                        ),
                    )
                    return True
                return False
            conn.execute(
                "INSERT INTO visits "
                "(path, referrer, user_agent, ip, verification_method, confidence) "
                "VALUES (?, ?, '', ?, ?, ?)",
                (
                    safe_path,
                    (referrer_host or "")[:255],
                    visitor_token[:64],
                    verification_method,
                    safe_confidence,
                ),
            )
            return True
    except Exception:
        return False


def analytics(days: int = 30) -> dict:
    """Aggregate confirmed visits and anonymous filter diagnostics."""
    days = max(1, min(days, ANALYTICS_RETENTION_DAYS))
    window = f"-{days} days"
    method_clause = (
        "verification_method = 'turnstile'"
        if settings.analytics_strict
        else "verification_method IN "
        "('turnstile', 'cloudflare_high_score', 'engaged_browser')"
    )
    visit_filter = (
        f"created_at >= datetime('now', ?) AND ip LIKE ? AND {method_clause}"
    )
    params = (window, f"{ANALYTICS_TOKEN_PREFIX}%")
    with db.get_conn() as conn:
        _prune(conn)
        per_day = conn.execute(
            "SELECT DATE(created_at) AS d, COUNT(*) AS c FROM visits "
            f"WHERE {visit_filter} GROUP BY d ORDER BY d",
            params,
        ).fetchall()
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM visits WHERE {visit_filter}", params
        ).fetchone()
        unique_visitors = conn.execute(
            "SELECT COUNT(DISTINCT ip) AS c FROM visits "
            f"WHERE {visit_filter}",
            params,
        ).fetchone()
        top_paths = conn.execute(
            "SELECT path, COUNT(*) AS c FROM visits "
            f"WHERE {visit_filter} GROUP BY path ORDER BY c DESC LIMIT 8",
            params,
        ).fetchall()
        top_refs = conn.execute(
            "SELECT referrer, COUNT(*) AS c FROM visits "
            f"WHERE {visit_filter} AND referrer != '' "
            "GROUP BY referrer ORDER BY c DESC LIMIT 8",
            params,
        ).fetchall()
        recent = conn.execute(
            "SELECT path, referrer, created_at, verification_method, confidence "
            f"FROM visits WHERE {visit_filter} ORDER BY id DESC LIMIT 15",
            params,
        ).fetchall()
        counter_rows = conn.execute(
            "SELECT reason, SUM(count) AS c FROM analytics_counters "
            "WHERE day >= DATE('now', ?) GROUP BY reason",
            (window,),
        ).fetchall()

    counters = {row["reason"]: int(row["c"]) for row in counter_rows}
    metric_opens = {
        "release_downloads": counters.get("metric_open_release_downloads", 0),
        "tracked_total_clones": counters.get(
            "metric_open_tracked_total_clones", 0
        ),
        "unique_cloners_14d": counters.get(
            "metric_open_unique_cloners_14d", 0
        ),
        "clones_14d": counters.get("metric_open_clones_14d", 0),
    }
    total_requests = counters.get("page_request", 0)
    confirmed = counters.get("confirmation_received", 0)
    seed_issued = counters.get("seed_issued", 0)
    diagnostics = {
        "total_requests": total_requests,
        "discarded_requests": max(total_requests - confirmed, 0),
        "confirmed": confirmed,
        "known_bot": counters.get("known_bot", 0),
        "missing_browser_confirmation": max(seed_issued - confirmed, 0),
        "turnstile_failed": counters.get("turnstile_failed", 0),
        "rate_limited": counters.get("rate_limited", 0),
        "invalid_seed": (
            counters.get("invalid_seed", 0)
            + counters.get("replayed_seed", 0)
        ),
        "missing_fetch_metadata": counters.get("missing_fetch_metadata", 0),
        "confirmation_rate": (
            round((confirmed / seed_issued) * 100, 1) if seed_issued else 0.0
        ),
    }
    total_visits = int(total["c"]) if total else 0
    visitor_days = int(unique_visitors["c"]) if unique_visitors else 0
    return {
        "days": days,
        "total_visits": total_visits,
        "unique_visitors": visitor_days,
        "confirmed_pageviews": total_visits,
        "confirmed_visitor_days": visitor_days,
        "per_day": [
            {"date": row["d"], "visits": int(row["c"])} for row in per_day
        ],
        "top_paths": [
            {"path": row["path"], "visits": int(row["c"])}
            for row in top_paths
        ],
        "top_referrers": [
            {"referrer": row["referrer"], "visits": int(row["c"])}
            for row in top_refs
        ],
        "recent": [
            {
                "path": row["path"],
                "referrer": row["referrer"],
                "at": row["created_at"],
                "verification_method": row["verification_method"],
                "confidence": int(row["confidence"]),
            }
            for row in recent
        ],
        "metric_opens": metric_opens,
        "diagnostics": diagnostics,
    }
