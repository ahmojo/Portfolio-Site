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
from .privacy import referrer_hostname

DB_PATH = Path("data/portfolio.db")
SESSION_SECRET_PATH = Path("data/.session_secret")
DB_LOCK = threading.RLock()

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
VALUES (1, 'learning FastAPI', 'building this very backend');

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
        "status": "learning FastAPI",
        "detail": "building this very backend",
    },
    "about": {
        "paragraphs": [
            "Ich bin <strong>Ahmet</strong>, 17 Jahre alt, aus dem Aargau. Seit der Bezirksschule interessiere ich mich für Informatik - deshalb die <span class=\"hl\">IMS</span>, aktuell im 2. Jahr.",
            "Mein Schwerpunkt liegt auf <strong>Backend-Entwicklung</strong>. Daneben interessiert mich Cybersecurity - ich lerne, wie Systeme funktionieren und wie man sie sicherer macht.",
            "Neben der Schule bilde ich mich selbständig weiter und lerne auch in meiner Freizeit gerne neue Informatik-Themen, zum Beispiel über Boot.dev. Im <span class=\"hl\">Praktikum im 4. Jahr</span> möchte ich dieses Wissen an echten Aufgaben anwenden und weiter ausbauen.",
        ],
    },
    "stats": [
        {"value": "2", "suffix": "nd", "label": "Jahr · IMS"},
        {"value": "4", "label": "Projekte"},
        {"value": "6", "label": "Zertifikate · Boot.dev"},
        {"value": "1", "decorator": "dot", "label": "Hackathon"},
    ],
    "skills": [
        {"key": "languages", "items": ["Python", "C#", "JavaScript", "HTML/CSS"]},
        {"key": "tools", "items": ["Docker", "Git", "PowerShell", "LiteDB", "MSSQL"]},
        {"key": "interests", "items": ["Backend", "Databases", "Cybersecurity", "Computer Vision", "Machine Learning"]},
    ],
    "projects": [
        {
            "title": "Regal-Erkennung für KMU",
            "desc": "Baden Hackt 2026 - ein System, das per <b style=\"color:var(--acc)\">YOLOv11n-cls</b> Produkte im Regal erkennt. Wird ein Produkt entnommen, löst es automatisch eine Bestellmail mit CSV-Anhang aus.",
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
                "## Das Problem\n"
                "Kleine KMU können sich professionelle Regalüberwachungssysteme kaum leisten. "
                "Leere Regalfächer bleiben oft unbemerkt, bis eine Kundin oder ein Kunde sie meldet.\n\n"
                "## Ansatz\n"
                "Eine Webcam beobachtet das Regal. Ein **YOLOv11n-cls** Modell klassifiziert jedes Fach "
                "in jedem Frame als voll oder leer. Sobald ein Produkt entnommen wird, löst FastAPI "
                "automatisch eine Bestellmail mit CSV-Anhang aus - vollautomatisches Nachbestellen.\n\n"
                "## Was ich gelernt habe\n"
                "- Echtzeit-Inferenz ist meistens die Kunst, *nicht* in jedem Frame zu inferieren.\n"
                "- Der eigentliche Mehrwert entsteht dort, wo ML-Output in eine profane Geschäftsaktion "
                "(eine E-Mail) übersetzt wird.\n\n"
                "> Gebaut in ~24h am **Baden Hackt 2026**."
            ),
        },
        {
            "title": "Dieses Portfolio",
            "desc": "Kein Template - das Frontend spricht mit einem eigenen <b style=\"color:var(--acc)\">FastAPI</b>-Backend: Live-GitHub-Stats, Projekt-Metadaten, ein Admin-Panel zum Bearbeiten der Inhalte und Uptime-Monitoring. Deployed on a self-managed Oracle Cloud VM.",
            "stack": "Python · FastAPI · SQLite · Docker · Oracle Cloud · Cloudflare",
            "repo": "",
            "featured": False,
            "badges": [{"label": "Full-Stack", "variant": "py"}],
            "slug": "portfolio",
            "content": (
                "## Idee\n"
                "Die meisten Portfolios sind statisch. Dieses hier ist ein kleines Full-Stack-Projekt: "
                "Die Inhalte, GitHub-Statistiken und Projekt-Metadaten kommen aus einem eigenen Backend.\n\n"
                "## Stack\n"
                "- **FastAPI** liefert Inhalte, GitHub-Stats, Projekt-Metadaten und Uptime aus.\n"
                "- **SQLite** speichert die editierbaren Inhalte; ein Admin-Panel schreibt sie per API.\n"
                "- **Docker** auf einer **Oracle-Cloud-VM**, ausgeliefert hinter **Cloudflare**.\n\n"
                "## Was ich gelernt habe\n"
                "- Wie man ein FastAPI-Backend strukturiert (Router, Auth, DB-Zugriff).\n"
                "- HMAC-signierte Session-Cookies und Rate-Limiting fürs Admin-Login.\n"
                "- Deployment und Betrieb: Docker, Reverse-Proxy, Monitoring.\n"
            ),
        },
        {
            "title": "Codex Claude Transfer",
            "desc": "Ein lokales CLI-Tool (<b style=\"color:var(--acc)\">cct</b>), das Codex- &amp; Claude-Code-Sessions zwischen Maschinen überträgt. Sessions als <code>.codexbundle</code> exportieren, kopieren, importieren - kein Cloud, kein Account, kein Server. Optionaler LAN-Sync.",
            "stack": "Go · Cobra · Indexed State · Local-Only",
            "repo": "ahmojo/codex-claude-transfer",
            "featured": False,
            "badges": [{"label": "Go · CLI", "variant": "py"}],
            "slug": "codex-claude-transfer",
            "content": (
                "## Das Problem\n"
                "Wer mit [Codex](https://github.com/openai/codex) oder "
                "[Claude Code](https://github.com/anthropics/claude-code) an mehreren Rechnern arbeitet, "
                "hat keine einfache Möglichkeit, Sessions zwischen Maschinen zu übertragen.\n\n"
                "## Ansatz\n"
                "`cct` ist ein kleines, rein lokales CLI. Du exportierst die Sessions eines Projekts in "
                "eine einzige `.codexbundle`-Datei, kopierst sie auf beliebigem Weg (USB-Stick, `scp`, "
                "Syncthing, verschlüsselte Festplatte) und importierst sie auf der anderen Maschine. "
                "**Keine Cloud, kein Account, kein Server** - und der Index/State des Agents bleibt unangetastet.\n\n"
                "## Features\n"
                "- Funktioniert mit **Codex** *und* **Claude Code** (inkl. Cross-Agent-Übergabe)\n"
                "- Inkrementeller Sync: nur Neues wird angehängt, nichts überschrieben\n"
                "- Secret-Scan &amp; Redaktion vor dem Export\n"
                "- Optionale Verschlüsselung der Bundles\n"
                "- Experimenteller LAN-Sync zwischen explizit gepairten Geräten\n\n"
                "> In Go geschrieben, mit [Cobra](https://github.com/spf13/cobra)."
            ),
        },
        {
            "title": "CLI-Agent mit Tool-Nutzung",
            "desc": "Ein CLI-Chatbot, der über die Google Gemini API Function Calling nutzt. Er kann Dateien lesen, schreiben und Python-Dateien in einem begrenzten Arbeitsbereich ausführen - gebaut als Lernprojekt im Boot.dev AI-Agent-Kurs.",
            "stack": "Python · Google GenAI SDK · Function Calling · uv",
            "repo": "ahmojo/AI_Agent",
            "featured": False,
            "badges": [{"label": "Python · Gemini API", "variant": "py"}],
            "slug": "cli-agent",
            "content": (
                "## Das Problem\n"
                "Wie funktioniert eigentlich Function Calling? Wie baut man einen Agenten, der selbstständig "
                "Werkzeuge aufruft, statt nur Text zurückzugeben?\n\n"
                "## Ansatz\n"
                "Ein Kommandozeilen-Programm schickt einen Prompt an Gemini und erlaubt dem Modell, eine "
                "Handvoll lokaler Werkzeuge aufzurufen:\n"
                "- Dateien und Verzeichnisse auflisten\n"
                "- Dateiinhalte lesen\n"
                "- Dateien schreiben oder überschreiben\n"
                "- Python-Dateien mit Argumenten ausführen\n\n"
                "Die Werkzeuge sind bewusst auf das Verzeichnis `./calculator` begrenzt, sodass der Agent "
                "in einem sicheren Sandkasten operiert. Über das GenAI SDK werden die Funktionsdeklarationen "
                "registriert und Modell-Aufrufe über `call_function.py` dispatcht.\n\n"
                "## Was ich gelernt habe\n"
                "- Wie ein Function-Calling-Loop aufgebaut ist (bis Text-Response oder Iterationslimit)\n"
                "- Warum ein begrenzter Arbeitsbereich essenziell für Sicherheit ist\n\n"
                "> Entstanden im [Boot.dev](https://www.boot.dev/) AI-Agent-Kurs."
            ),
        },
        {
            "title": "Machine Learning",
            "desc": "Machine-Learning-Schulprojekt (LB-259): Vorhersage von Hauspreisen in Kalifornien als Regressionsproblem. Datenanalyse, Modelltraining und Evaluation in Jupyter Notebooks mit scikit-learn.",
            "stack": "Python · Jupyter · scikit-learn · Pandas",
            "repo": "ahmojo/LB-259_machine_learning",
            "featured": False,
            "badges": [{"label": "ML · Jupyter", "variant": "ml"}],
            "slug": "machine-learning",
            "content": (
                "## Aufgabe\n"
                "Vorhersage des mittleren Hauswerts (`median_house_value`) anhand von Features wie "
                "Einkommen, Alter, Zimmerzahl und Nähe zum Meer - ein klassisches "
                "**Regressionsproblem**.\n\n"
                "## Datensatz\n"
                "California Housing Prices (StatLib / Volkszählung Kalifornien 1990, CC0). "
                "Enthält geografische Koordinaten, demografische und wirtschaftliche Merkmale pro Gebiet.\n\n"
                "## Vorgehen\n"
                "- **Datenanalyse** (`data_description.ipynb`): Verteilungen, Korrelationen, Ausreisser\n"
                "- **Modell** (`model.ipynb`): Training mit scikit-learn\n"
                "- **Evaluation** (`evaluation.ipynb`): Metriken, Fehleranalyse\n\n"
                "## Was ich gelernt habe\n"
                "- Wie ein vollständiges ML-Projekt von den Rohdaten bis zur Bewertung abläuft\n"
                "- Welche Rolle Feature-Auswahl und Datenvorverarbeitung spielen\n\n"
                "> Schulprojekt, LB-259 - erster richtiger Kontakt mit Machine Learning."
            ),
        },
    ],
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
        "accent": "#6de6a2",
        "ink": "#e6edf8",
        "particles": 72,
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
                is_daily_hash = (
                    len(stored_ip) == 32
                    and all(char in "0123456789abcdef" for char in stored_ip)
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
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO visits (path, referrer, user_agent, ip) VALUES (?, ?, '', ?)",
                (
                    path[:255] or "/",
                    (referrer_host or "")[:255],
                    (visitor_hash or "")[:64],
                ),
            )
    except Exception:
        pass  # analytics must never break a request


def analytics(days: int = 30) -> dict:
    """Aggregate visit data for the admin dashboard."""
    days = max(1, min(days, 365))
    with get_conn() as conn:
        # total + per-day counts over the window
        per_day = conn.execute(
            "SELECT DATE(created_at) AS d, COUNT(*) AS c FROM visits "
            "WHERE created_at >= datetime('now', ?) "
            "GROUP BY d ORDER BY d",
            (f"-{days} days",),
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) AS c FROM visits").fetchone()
        unique_visitors = conn.execute(
            "SELECT COUNT(DISTINCT ip) AS c FROM visits "
            "WHERE created_at >= datetime('now', ?) AND ip != ''",
            (f"-{days} days",),
        ).fetchone()
        top_paths = conn.execute(
            "SELECT path, COUNT(*) AS c FROM visits "
            "WHERE created_at >= datetime('now', ?) "
            "GROUP BY path ORDER BY c DESC LIMIT 8",
            (f"-{days} days",),
        ).fetchall()
        top_refs = conn.execute(
            "SELECT referrer, COUNT(*) AS c FROM visits "
            "WHERE created_at >= datetime('now', ?) AND referrer != '' "
            "GROUP BY referrer ORDER BY c DESC LIMIT 8",
            (f"-{days} days",),
        ).fetchall()
        recent = conn.execute(
            "SELECT path, referrer, created_at FROM visits "
            "ORDER BY id DESC LIMIT 15"
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
