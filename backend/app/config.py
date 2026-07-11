"""Configuration for the portfolio backend.

Local development keeps convenient defaults. Production Docker sets
PORTFOLIO_ENV=production and refuses dangerous placeholder secrets.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="PORTFOLIO_", extra="ignore"
    )

    # --- server ---
    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    expose_docs: bool = True

    # --- cors: the origins allowed to call the API ---
    # local dev = the static site served from any origin / file://
    allowed_origins: list[str] = [
        "http://localhost:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        "null",  # file:// origin shows up as "null"
    ]

    # --- github ---
    github_user: str = "ahmojo"
    github_token: str = ""  # optional, raises rate limit from 60 -> 5000/hr
    projects: dict[str, str] = {
        "Regal-Erkennung für KMU": "ahmojo/Badenhackt_KMU_Trifft_KI",
        "Codex Claude Transfer": "ahmojo/codex-claude-transfer",
        "CLI-Agent mit Tool-Nutzung": "ahmojo/AI_Agent",
        "Machine Learning": "ahmojo/LB-259_machine_learning",
    }
    projects_ttl: int = 600

    # --- "now" endpoint ---
    # Leave empty only for local development.
    now_token: str = ""

    # --- uptime badge ---
    # API key stays server-side. Leave empty to show local self-hosted status.
    uptime_robot_api_key: str = ""
    uptime_robot_monitor_id: str = ""
    uptime_robot_status_page_url: str = "https://stats.uptimerobot.com/PFy2MRBznP"
    uptime_cache_seconds: int = 300

    # --- admin auth ---
    admin_password: str = "admin"
    session_secret: str = ""
    session_ttl_hours: int = 12
    session_cookie: str = "portfolio_admin"
    secure_cookies: bool = False
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300

    @property
    def database_url(self) -> str:
        return "sqlite:///./data/portfolio.db"

    @property
    def is_production(self) -> bool:
        return self.env.strip().lower() in {"prod", "production"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


_UNSAFE_ADMIN_PASSWORDS = {
    "",
    "admin",
    "password",
    "changeme",
    "change-me",
    "change-this-before-deploy",
    "change-this-to-a-long-random-password",
}

_UNSAFE_SESSION_SECRETS = {
    "",
    "change-this-to-a-long-random-session-secret",
}

_FORBIDDEN_PRODUCTION_ORIGINS = {"*", "null"}


def validate_production_settings() -> None:
    """Fail closed on public deployments with unsafe secrets or CORS."""
    if not settings.is_production:
        return

    password = settings.admin_password.strip()
    if password.lower() in _UNSAFE_ADMIN_PASSWORDS or len(password) < 12:
        raise RuntimeError(
            "Unsafe production admin password. Set PORTFOLIO_ADMIN_PASSWORD "
            "to a unique password with at least 12 characters."
        )

    session_secret = settings.session_secret.strip()
    if session_secret.lower() in _UNSAFE_SESSION_SECRETS or len(session_secret) < 32:
        raise RuntimeError(
            "PORTFOLIO_SESSION_SECRET is too short for production. Use a "
            "random value with at least 32 characters."
        )

    if not settings.now_token.strip():
        raise RuntimeError(
            "PORTFOLIO_NOW_TOKEN must be set in production so PUT /api/now "
            "cannot be modified by anonymous visitors."
        )

    if any(origin in _FORBIDDEN_PRODUCTION_ORIGINS for origin in settings.allowed_origins):
        raise RuntimeError(
            "Unsafe production CORS origins. Remove '*'/null origins and use "
            "the real https:// domain only."
        )
