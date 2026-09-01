"""Private SQLite persistence for portfolio feedback."""
from __future__ import annotations

from . import db

FEEDBACK_RETENTION_DAYS = 180
MAX_RECENT_FEEDBACK = 50
_RATINGS = {"positive", "negative"}
_SOURCES = {
    "",
    "linkedin",
    "github",
    "bootdev",
    "recruiting",
    "search",
    "recommendation",
    "other",
}


def init_feedback_schema() -> None:
    """Create the feedback table for fresh and older database snapshots."""
    with db.get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                rating     TEXT    NOT NULL CHECK (rating IN ('positive', 'negative')),
                comment    TEXT    NOT NULL DEFAULT '',
                source     TEXT    NOT NULL DEFAULT '',
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at);
            """
        )
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(feedback)")
        }
        if "source" not in columns:
            conn.execute(
                "ALTER TABLE feedback ADD COLUMN source TEXT NOT NULL DEFAULT ''"
            )
        _prune(conn)


def _prune(conn) -> None:
    conn.execute(
        "DELETE FROM feedback WHERE created_at < datetime('now', ?)",
        (f"-{FEEDBACK_RETENTION_DAYS} days",),
    )


def record_feedback(rating: str, comment: str, source: str = "") -> None:
    """Store the rating, optional discovery source, comment, and UTC timestamp."""
    if rating not in _RATINGS:
        raise ValueError("invalid feedback rating")
    if source not in _SOURCES:
        raise ValueError("invalid feedback source")
    with db.get_conn() as conn:
        _prune(conn)
        conn.execute(
            "INSERT INTO feedback (rating, comment, source) VALUES (?, ?, ?)",
            (rating, comment, source),
        )


def feedback_summary() -> dict:
    """Return the small, admin-only feedback view."""
    with db.get_conn() as conn:
        _prune(conn)
        counts = {
            row["rating"]: int(row["count"])
            for row in conn.execute(
                "SELECT rating, COUNT(*) AS count FROM feedback GROUP BY rating"
            ).fetchall()
        }
        total = sum(counts.values())
        positive = counts.get("positive", 0)
        recent = conn.execute(
            "SELECT rating, comment, source, created_at FROM feedback "
            "ORDER BY id DESC LIMIT ?",
            (MAX_RECENT_FEEDBACK,),
        ).fetchall()

    return {
        "total": total,
        "positive": positive,
        "negative": counts.get("negative", 0),
        "positive_ratio": round((positive / total) * 100, 1) if total else 0.0,
        "recent": [dict(row) for row in recent],
    }
