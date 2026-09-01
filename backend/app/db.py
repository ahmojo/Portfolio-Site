"""SQLite database setup + lightweight schema bootstrapper.

Uses stdlib sqlite3 — no ORM needed for a portfolio backend. The db file lives
in ./data/portfolio.db (created on first run).
"""
from __future__ import annotations

import json
import os
import secrets
import shutil
import sqlite3
import threading
import uuid
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import settings
from .models import OPEN_SOURCE_DEFAULTS
from .privacy import referrer_hostname

DB_PATH = Path("data/portfolio.db")
SESSION_SECRET_PATH = Path("data/.session_secret")
DB_LOCK = threading.RLock()
ANALYTICS_RETENTION_DAYS = 90
ANALYTICS_TOKEN_PREFIX = "h1:"

EXPECTED_SCHEMA = {
    "now_state": {"id", "status", "detail", "updated_at"},
    "content": {"key", "data", "updated_at"},
    "visits": {
        "id",
        "path",
        "referrer",
        "user_agent",
        "ip",
        "country",
        "created_at",
    },
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS now_state (
    id         INTEGER PRIMARY KEY CHECK (id = 1),
    status     TEXT    NOT NULL DEFAULT '',
    detail     TEXT    NOT NULL DEFAULT '',
    updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- single-row "current status" seeded on first run
INSERT OR IGNORE INTO now_state (id, status, detail)
VALUES (1, 'a webgame', '');

CREATE TABLE IF NOT EXISTS content (
    key         TEXT PRIMARY KEY,
    data        TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS visits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT    NOT NULL DEFAULT '/',
    referrer    TEXT    NOT NULL DEFAULT '',
    user_agent  TEXT    NOT NULL DEFAULT '',
    ip          TEXT    NOT NULL DEFAULT '',
    country     TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_visits_created ON visits(created_at);
CREATE INDEX IF NOT EXISTS idx_visits_path ON visits(path);
CREATE INDEX IF NOT EXISTS idx_visits_token_path_created
    ON visits(ip, path, created_at);

CREATE TABLE IF NOT EXISTS feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    rating     TEXT    NOT NULL CHECK (rating IN ('positive', 'negative')),
    comment    TEXT    NOT NULL DEFAULT '',
    source     TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at);
"""

# Default site content, seeded into the `content` table on first boot.
# This mirrors the current static index.html so nothing changes until edited.
DEFAULT_CONTENT = {
    "hero": {
        "name": "Ahmet",
        "lede": "<strong>IMS-Schüler mit Backend-Fokus</strong> aus der Schweiz. Ich baue am liebsten Dinge, die einfach zuverlässig laufen - mit Python, C# und JavaScript.",
        "phrases": [
            "Backend · Python · C# · JavaScript",
            "building things that should just run.",
        ],
    },
    "now": {
        "status": "a webgame",
        "detail": "",
    },
    "about": {
        "paragraphs": [
            "Ich bin <strong>Ahmet</strong>, 18 Jahre alt, aus dem Aargau. Seit der Bezirksschule interessiere ich mich für Informatik - deshalb die <span class=\"hl\">IMS</span>, aktuell im 3. Jahr.",
            "Mein Schwerpunkt liegt auf <strong>Backend-Entwicklung</strong>. Daneben interessiert mich Cybersecurity - ich lerne, wie Systeme funktionieren und wie man sie sicherer macht.",
            "Neben der Schule bilde ich mich selbständig weiter und lerne auch in meiner Freizeit gerne neue Informatik-Themen, zum Beispiel über Boot.dev. Im <span class=\"hl\">Praktikum im 4. Jahr</span> möchte ich dieses Wissen an echten Aufgaben anwenden und weiter ausbauen.",
        ],
    },
    "stats": [
        {"value": "3", "suffix": "rd", "label": "Jahr · IMS"},
        {"value": "5", "label": "Projekte"},
        {"value": "6", "label": "Zertifikate · Boot.dev"},
        {"value": "1", "decorator": "", "label": "Hackathon"},
    ],
    "skills": [
        {"key": "languages", "items": ["Python", "C#", "JavaScript", "HTML/CSS"]},
        {"key": "tools", "items": ["Docker", "Git", "PowerShell", "LiteDB", "MSSQL"]},
        {"key": "interests", "items": ["Backend", "Databases", "Cybersecurity", "Computer Vision", "Machine Learning"]},
    ],
    "projects": [
        {
            "title": "Regal-Erkennung für KMU",
            "desc": "Hackathon-Prototyp für kleine Betriebe. Eine Webcam prüft mit <b style=\"color:var(--acc)\">YOLOv11n-cls</b> eingerichtete Regalplätze. Fehlt ein Produkt bei mehreren Scans, kann FastAPI eine Bestellmail mit CSV-Anhang senden.",
            "stack": "Python · FastAPI · YOLOv11n-cls · OpenCV · uvicorn",
            "repo": "ahmojo/Badenhackt_KMU_Trifft_KI",
            "featured": True,
            "media": "vids/video.mp4",
            "badges": [
                {"label": "Hackathon", "variant": "hack"},
                {"label": "Computer Vision", "variant": "cv"},
            ],
            "slug": "regal-erkennung",
            "content": (
                "## Problem\n"
                "Leere Regalplätze werden leicht übersehen. Der Prototyp erkennt fehlende Produkte bei wiederholten Kamerascans und kann eine Nachbestellung auslösen.\n\n"
                "## Architektur\n"
                "Der Browser wählt Kamera und Regalplätze. **YOLOv11n-cls** klassifiziert sichtbare Produkte. "
                "**FastAPI** verarbeitet die Scans und kann eine Bestellmail mit CSV-Anhang senden.\n\n"
                "## Stand\n"
                "Hackathon-Prototyp. Modellgewichte und Demo-Dateien liegen wegen ihrer Größe nicht im Repository."
            ),
        },
        {
            "title": "Codex Claude Transfer",
            "desc": "<b style=\"color:var(--acc)\">cct</b> überträgt lokale Codex- und Claude-Code-Sitzungen zwischen Rechnern. Es bündelt sie als <code>.codexbundle</code>, prüft die Prüfsumme und importiert sie am Ziel. Standardmäßig braucht es keinen Cloud-Dienst.",
            "stack": "Go · Cobra · Indexed State · Local-Only",
            "repo": "ahmojo/codex-claude-transfer",
            "featured": False,
            "badges": [{"label": "Go · CLI", "variant": "py"}],
            "slug": "codex-claude-transfer",
            "content": (
                "## Problem\n"
                "Codex und Claude Code speichern Sitzungen lokal. Beim Rechner- oder Agentwechsel fehlt sonst ein einfacher Weg, den Projektkontext mitzunehmen.\n\n"
                "## Architektur\n"
                "`cct` liest lokale Sitzungsdateien, bündelt sie in einer `.codexbundle` und prüft die Datei vor dem Import. "
                "Die Indexdatenbanken der Agents werden nicht direkt geändert; sie lesen importierte Dateien später neu ein.\n\n"
                "## Nutzung\n"
                "```\n"
                "cct export --project .\n"
                "cct import ./project.codexbundle --dry-run\n"
                "cct import ./project.codexbundle\n"
                "```\n\n"
                "## Funktionen\n"
                "- Export und Import für Codex und Claude Code\n"
                "- Übergabe zwischen beiden Agents\n"
                "- CLI, Terminal-Assistent und lokale Browser-App\n"
                "- Secret-Prüfung, optionale Verschlüsselung und LAN-Sync\n\n"
                "## Hinweis\n"
                "Bundles können Prompts, Code und Zugangsdaten enthalten. Du solltest sie wie private Arbeitsdaten behandeln."
            ),
        },
        {
            "title": "Dieses Portfolio",
            "desc": "Meine Portfolio-Seite mit eigenem <b style=\"color:var(--acc)\">FastAPI</b>-Backend. Das Backend liefert Inhalte, GitHub-Daten und Statuswerte. Ein geschützter Admin-Bereich verwaltet die Texte. Docker betreibt die Anwendung auf einer Oracle-Cloud-VM.",
            "stack": "Python · FastAPI · SQLite · Docker · Oracle Cloud · Cloudflare",
            "repo": "ahmojo/Portfolio-Site",
            "featured": False,
            "badges": [{"label": "Full-Stack", "variant": "py"}],
            "slug": "portfolio",
            "content": (
                "## Architektur\n"
                "Frontend und Admin-Panel verwenden die FastAPI-API auf derselben Origin. Das Backend liefert statische Dateien, "
                "editierbare Inhalte, Projektdaten sowie GitHub- und Uptime-Status. SQLite speichert Inhalte und reduzierte Analysedaten.\n\n"
                "## Nutzung\n"
                "Im geschützten Admin-Bereich lassen sich Hero, Über mich, Skills und Projekte bearbeiten. "
                "Die öffentliche Seite lädt diese Daten über `/api/content`.\n\n"
                "## Betrieb\n"
                "Docker Compose läuft auf einer Oracle-Cloud-VM. Cloudflare übernimmt DNS, HTTPS und CDN. "
                "Das Backend speichert keine vollständigen IP-Adressen."
            ),
        },
        {
            "title": "CLI-Agent mit Tool-Nutzung",
            "desc": "Lernprojekt aus dem Boot.dev-Kurs. Ein Python-Programm sendet Aufgaben an Gemini und stellt vier lokale Werkzeuge bereit. Der Agent arbeitet nur im Ordner `./calculator` und kann dort Dateien lesen, ändern und Python ausführen.",
            "stack": "Python · Google GenAI SDK · Function Calling · uv",
            "repo": "ahmojo/AI_Agent",
            "featured": False,
            "badges": [{"label": "Python · Gemini API", "variant": "py"}],
            "slug": "cli-agent",
            "content": (
                "## Architektur\n"
                "Das Terminalprogramm sendet Anfragen über das Google GenAI SDK an Gemini. Function Calling wählt eines von vier lokalen Werkzeugen; "
                "`call_function.py` ordnet den Aufruf der passenden Python-Funktion zu. Die Werkzeuge arbeiten nur in `./calculator`.\n\n"
                "## Nutzung\n"
                "Das Programm kann:\n"
                "- Dateien und Verzeichnisse auflisten\n"
                "- Dateiinhalte lesen\n"
                "- Dateien schreiben oder überschreiben\n"
                "- Python-Dateien mit Argumenten ausführen\n\n"
                "## Stand\n"
                "Das Repository ist ein Lernprojekt aus dem Boot.dev-Kurs, kein fertiger Coding-Agent. "
                "Modellgesteuerte Dateiänderungen und Python-Ausführung bleiben riskant."
            ),
        },
        {
            "title": "Machine Learning",
            "desc": "Schulprojekt zur Vorhersage mittlerer Hauswerte in Kalifornien. Drei Jupyter Notebooks dokumentieren Datenprüfung, Modelltraining und Auswertung mit scikit-learn.",
            "stack": "Python · Jupyter · scikit-learn · Pandas",
            "repo": "ahmojo/LB-259_machine_learning",
            "featured": False,
            "badges": [{"label": "ML · Jupyter", "variant": "ml"}],
            "slug": "machine-learning",
            "content": (
                "## Architektur\n"
                "Der Ablauf geht vom California-Housing-Datensatz über Datenprüfung und Modelltraining zur Auswertung. "
                "Drei Jupyter Notebooks teilen diese Schritte auf.\n\n"
                "## Projekt\n"
                "Ein Regressionsmodell sagt den mittleren Hauswert (`median_house_value`) eines Gebiets voraus. "
                "Als Eingaben dienen unter anderem Einkommen, Hausalter, Zimmerzahl und Lage.\n\n"
                "## Datensatz\n"
                "Das Projekt nutzt den Datensatz California Housing Prices aus StatLib und der kalifornischen Volkszählung von 1990. "
                "Die Werte beschreiben Gebiete und enthalten keine Namen oder Kontaktdaten.\n\n"
                "## Stand\n"
                "Schulprojekt. Die Notebooks dokumentieren den Lern- und Auswertungsprozess."
            ),
        },
    ],
    "open_source": [dict(item) for item in OPEN_SOURCE_DEFAULTS],
    "open_source_hidden": [],
    "learning": [
        {"kind": "Project", "name": "Build an AI Agent", "date": "Apr 2026", "type": "url", "url": "https://github.com/ahmojo/AI_Agent"},
        {"kind": "Course", "name": "Learn Functional Programming in Python", "date": "Apr 22 · 2026", "type": "preview", "src": "new_image/bootdev_certificate.png", "title": "Learn Functional Programming in Python - Certificate"},
        {"kind": "Project", "name": "Build Asteroids", "date": "Mar 2026", "type": "url", "url": "https://github.com/ahmojo/asteroid"},
        {"kind": "Course", "name": "Learn Object Oriented Programming in Python", "date": "Mar 11 · 2026", "type": "preview", "src": "new_image/bootdev_certificate (3).png", "title": "Learn Object Oriented Programming in Python - Certificate"},
        {"kind": "Course", "name": "Learn Git", "date": "Mar 01 · 2026", "type": "preview", "src": "new_image/bootdev_certificate (5).png", "title": "Learn Git - Certificate"},
        {"kind": "Course", "name": "Learn Linux", "date": "Feb 14 · 2026", "type": "preview", "src": "new_image/bootdev_certificate (4).png", "title": "Learn Linux - Certificate"},
        {"kind": "Course", "name": "Learn Docker", "date": "Feb 11 · 2026", "type": "preview", "src": "new_image/bootdev_certificate (1).png", "title": "Learn Docker - Certificate"},
        {"kind": "Project", "name": "Build a Bookbot", "date": "Feb 2026", "type": "url", "url": "https://github.com/ahmojo/Bookbot"},
        {"kind": "Course", "name": "Introduction to Python Course", "date": "Feb 05 · 2026", "type": "preview", "src": "new_image/bootdev_certificate (2).png", "title": "Introduction to Python Course - Certificate"},
    ],
    "theme": {
        "bg": "#161a28",
        "surface": "#232840",
        "accent": "#6de6a2",
        "accent_alt": "#7db2ee",
        "ink": "#e6edf8",
        "background_style": "ambient",
        "decoration": "none",
        "decoration_intensity": 58,
        "button_style": "gradient",
        "button_animation": "shine",
        "gradient_angle": 120,
        "radius": 8,
        "content_width": 820,
        "motion": "full",
        "grain": 10,
    },
    "cct_metrics": {
        "release_downloads": True,
        "tracked_total_clones": True,
        "unique_cloners_14d": True,
        "clones_14d": True,
    },
}


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DB_LOCK:
        with closing(_conn()) as conn:
            conn.executescript(SCHEMA)
            # One-time/ongoing privacy migration for rows created by older
            # versions that stored raw IPs, full referrers, and User-Agents.
            rows = conn.execute(
                "SELECT id, referrer, ip FROM visits "
                "WHERE user_agent != '' OR referrer LIKE '%/%' OR ip != ''"
            ).fetchall()
            for row in rows:
                stored_ip = row["ip"] or ""
                stored_referrer = row["referrer"] or ""
                reduced_referrer = referrer_hostname(stored_referrer)
                if not reduced_referrer and stored_referrer and "/" not in stored_referrer:
                    reduced_referrer = referrer_hostname(
                        f"https://{stored_referrer}"
                    )
                hash_value = stored_ip.removeprefix(ANALYTICS_TOKEN_PREFIX)
                is_daily_hash = (
                    len(hash_value) == 32
                    and all(char in "0123456789abcdef" for char in hash_value)
                )
                conn.execute(
                    "UPDATE visits SET referrer = ?, user_agent = '', ip = ? "
                    "WHERE id = ?",
                    (
                        reduced_referrer,
                        stored_ip if is_daily_hash else "",
                        row["id"],
                    ),
                )
            # seed the site content snapshot on first boot
            conn.execute(
                "INSERT OR IGNORE INTO content (key, data) VALUES (?, ?)",
                ("site", json.dumps(DEFAULT_CONTENT)),
            )
            conn.commit()


def get_session_secret() -> str:
    """Return the HMAC signing secret, persisting a random one on first run."""
    if settings.session_secret:
        return settings.session_secret
    SESSION_SECRET_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SESSION_SECRET_PATH.exists():
        return SESSION_SECRET_PATH.read_text().strip()
    secret = secrets.token_urlsafe(48)
    SESSION_SECRET_PATH.write_text(secret)
    return secret


def load_content() -> dict:
    """Read the site content blob (or the default if missing)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT data FROM content WHERE key = 'site'"
        ).fetchone()
    if row:
        try:
            return json.loads(row["data"])
        except (json.JSONDecodeError, TypeError):
            pass
    return DEFAULT_CONTENT


def save_content(data: dict) -> None:
    """Replace the site content blob."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO content (key, data, updated_at) VALUES ('site', ?, datetime('now')) "
            "ON CONFLICT(key) DO UPDATE SET data = excluded.data, updated_at = datetime('now')",
            (json.dumps(data),),
        )


def _conn() -> sqlite3.Connection:
    # check_same_thread=False: FastAPI may touch the db from threadpool workers.
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # WAL keeps reads non-blocking when the dev server hammers it.
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


@contextmanager
def get_conn():
    """Yield a connection, auto-commit on success, rollback on error."""
    with DB_LOCK:
        conn = _conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def record_visit(path: str, referrer_host: str, visitor_hash: str) -> None:
    """Persist a privacy-reduced page visit; never raise to the caller.

    The legacy ``ip`` column stores only a daily, keyed hash. Raw IP addresses
    and User-Agent strings are deliberately not retained.
    """
    if not visitor_hash:
        return
    visitor_token = f"{ANALYTICS_TOKEN_PREFIX}{visitor_hash}"
    try:
        with get_conn() as conn:
            conn.execute(
                "DELETE FROM visits WHERE created_at < datetime('now', ?)",
                (f"-{ANALYTICS_RETENTION_DAYS} days",),
            )
            already_counted = conn.execute(
                "SELECT 1 FROM visits "
                "WHERE path = ? AND ip = ? AND DATE(created_at) = DATE('now') "
                "LIMIT 1",
                (path[:255] or "/", visitor_token),
            ).fetchone()
            if already_counted:
                return
            conn.execute(
                "INSERT INTO visits (path, referrer, user_agent, ip) VALUES (?, ?, '', ?)",
                (
                    path[:255] or "/",
                    (referrer_host or "")[:255],
                    visitor_token[:64],
                ),
            )
    except Exception:
        pass  # analytics must never break a request


def analytics(days: int = 30) -> dict:
    """Aggregate visit data for the admin dashboard."""
    days = max(1, min(days, 365))
    window = f"-{days} days"
    human_token = f"{ANALYTICS_TOKEN_PREFIX}%"
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM visits WHERE created_at < datetime('now', ?)",
            (f"-{ANALYTICS_RETENTION_DAYS} days",),
        )
        per_day = conn.execute(
            "SELECT DATE(created_at) AS d, COUNT(*) AS c FROM visits "
            "WHERE created_at >= datetime('now', ?) AND ip LIKE ? "
            "GROUP BY d ORDER BY d",
            (window, human_token),
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM visits "
            "WHERE created_at >= datetime('now', ?) AND ip LIKE ?",
            (window, human_token),
        ).fetchone()
        unique_visitors = conn.execute(
            "SELECT COUNT(DISTINCT ip) AS c FROM visits "
            "WHERE created_at >= datetime('now', ?) AND ip LIKE ?",
            (window, human_token),
        ).fetchone()
        top_paths = conn.execute(
            "SELECT path, COUNT(*) AS c FROM visits "
            "WHERE created_at >= datetime('now', ?) AND ip LIKE ? "
            "GROUP BY path ORDER BY c DESC LIMIT 8",
            (window, human_token),
        ).fetchall()
        top_refs = conn.execute(
            "SELECT referrer, COUNT(*) AS c FROM visits "
            "WHERE created_at >= datetime('now', ?) AND ip LIKE ? "
            "AND referrer != '' "
            "GROUP BY referrer ORDER BY c DESC LIMIT 8",
            (window, human_token),
        ).fetchall()
        recent = conn.execute(
            "SELECT path, referrer, created_at FROM visits "
            "WHERE created_at >= datetime('now', ?) AND ip LIKE ? "
            "ORDER BY id DESC LIMIT 15",
            (window, human_token),
        ).fetchall()
    return {
        "days": days,
        "total_visits": int(total["c"]) if total else 0,
        "unique_visitors": int(unique_visitors["c"]) if unique_visitors else 0,
        "per_day": [{"date": r["d"], "visits": int(r["c"])} for r in per_day],
        "top_paths": [{"path": r["path"], "visits": int(r["c"])} for r in top_paths],
        "top_referrers": [{"referrer": r["referrer"], "visits": int(r["c"])} for r in top_refs],
        "recent": [{"path": r["path"], "referrer": r["referrer"],
                    "at": r["created_at"]} for r in recent],
    }


class RestoreValidationError(ValueError):
    """Raised when an uploaded database cannot safely replace the active DB."""


def _readonly_connection(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def validate_restore_candidate(path: Path) -> None:
    """Validate integrity, expected schema, and required application data."""
    try:
        with closing(_readonly_connection(path)) as conn:
            integrity_rows = conn.execute("PRAGMA integrity_check").fetchall()
            if not integrity_rows or any(row[0] != "ok" for row in integrity_rows):
                raise RestoreValidationError("database integrity check failed")

            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            missing_tables = set(EXPECTED_SCHEMA) - tables
            if missing_tables:
                names = ", ".join(sorted(missing_tables))
                raise RestoreValidationError(f"database schema is missing: {names}")

            for table, expected_columns in EXPECTED_SCHEMA.items():
                columns = {
                    row["name"]
                    for row in conn.execute(f'PRAGMA table_info("{table}")')
                }
                missing_columns = expected_columns - columns
                if missing_columns:
                    names = ", ".join(sorted(missing_columns))
                    raise RestoreValidationError(
                        f"table {table} is missing columns: {names}"
                    )

            content_row = conn.execute(
                "SELECT data FROM content WHERE key = 'site'"
            ).fetchone()
            if content_row is None:
                raise RestoreValidationError("database has no site content")
            content = json.loads(content_row["data"])
            if not isinstance(content, dict):
                raise RestoreValidationError("site content must be a JSON object")

            now_row = conn.execute(
                "SELECT id FROM now_state WHERE id = 1"
            ).fetchone()
            if now_row is None:
                raise RestoreValidationError("database has no current status row")

            conn.execute("SELECT COUNT(*) FROM visits").fetchone()
    except RestoreValidationError:
        raise
    except (json.JSONDecodeError, sqlite3.Error, OSError) as exc:
        raise RestoreValidationError("database validation failed") from exc


def _remove_sqlite_sidecars(path: Path) -> None:
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{path}{suffix}")
        try:
            sidecar.unlink()
        except FileNotFoundError:
            pass


def _backup_active_database(destination: Path) -> None:
    with closing(sqlite3.connect(DB_PATH)) as source:
        with closing(sqlite3.connect(destination)) as target:
            source.backup(target)


def restore_database(candidate_path: Path) -> tuple[int, Path]:
    """Atomically replace the active DB and roll back on any post-swap failure."""
    candidate_path = candidate_path.resolve()
    validate_restore_candidate(candidate_path)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = DB_PATH.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"portfolio-before-restore-{stamp}-{uuid.uuid4().hex[:8]}.db"
    rollback_path = DB_PATH.parent / f".portfolio-rollback-{uuid.uuid4().hex}.db"

    with DB_LOCK:
        _backup_active_database(backup_path)
        try:
            _remove_sqlite_sidecars(DB_PATH)
            os.replace(candidate_path, DB_PATH)
            validate_restore_candidate(DB_PATH)
        except Exception:
            shutil.copy2(backup_path, rollback_path)
            _remove_sqlite_sidecars(DB_PATH)
            os.replace(rollback_path, DB_PATH)
            validate_restore_candidate(DB_PATH)
            raise
        finally:
            try:
                rollback_path.unlink()
            except FileNotFoundError:
                pass

    return DB_PATH.stat().st_size, backup_path
