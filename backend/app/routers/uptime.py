"""Public uptime/status summary for the portfolio homepage.

UptimeRobot API keys must stay server-side. This endpoint gives the frontend a
safe, tiny JSON shape and falls back to local health when no provider is set.
"""
from __future__ import annotations

import time
from typing import Any

import httpx
from fastapi import APIRouter

from ..config import settings


router = APIRouter(prefix="/api/uptime", tags=["uptime"])

_CACHE: dict[str, Any] = {"until": 0.0, "data": None}
_UPTIMEROBOT_URL = "https://api.uptimerobot.com/v2/getMonitors"
_STATUS_TEXT = {
    0: ("paused", "paused"),
    1: ("pending", "not checked yet"),
    2: ("up", "online"),
    8: ("down", "seems down"),
    9: ("down", "offline"),
}


def _base_status(source: str, configured: bool) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "up",
        "status_text": "online",
        "source": source,
        "configured": configured,
        "uptime_7d": None,
        "uptime_30d": None,
        "response_time_ms": None,
        "status_page_url": settings.uptime_robot_status_page_url,
        "checked_url": "https://ahmet-portfolio.ch/api/health",
        "self_hosted": {
            "edge": "Cloudflare HTTPS",
            "host": "Oracle Always Free VM",
            "runtime": "Docker · FastAPI · SQLite",
        },
    }


def _first_monitor(payload: dict[str, Any]) -> dict[str, Any] | None:
    monitors = payload.get("monitors")
    if isinstance(monitors, list) and monitors:
        return monitors[0]
    return None


def _uptime_ratio(monitor: dict[str, Any], index: int) -> str | None:
    ratios = monitor.get("custom_uptime_ratio")
    if isinstance(ratios, str):
        parts = [part.strip() for part in ratios.split("-")]
        if index < len(parts) and parts[index]:
            return parts[index]
    return None


def _latest_response_time(monitor: dict[str, Any]) -> int | None:
    response_times = monitor.get("response_times")
    if isinstance(response_times, list) and response_times:
        value = response_times[-1].get("value")
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    value = monitor.get("average_response_time")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


async def _from_uptimerobot() -> dict[str, Any]:
    payload = {
        "api_key": settings.uptime_robot_api_key,
        "format": "json",
        "logs": "0",
        "response_times": "1",
        "response_times_limit": "1",
        "custom_uptime_ratios": "7-30",
    }
    if settings.uptime_robot_monitor_id.strip():
        payload["monitors"] = settings.uptime_robot_monitor_id.strip()

    async with httpx.AsyncClient(timeout=4.0) as client:
        response = await client.post(_UPTIMEROBOT_URL, data=payload)
        response.raise_for_status()
        body = response.json()

    monitor = _first_monitor(body)
    if not monitor:
        data = _base_status("uptimerobot", True)
        data.update({"status": "unknown", "status_text": "monitor not found", "ok": False})
        return data

    status_code = monitor.get("status")
    try:
        status_code = int(status_code)
    except (TypeError, ValueError):
        status_code = -1
    status, status_text = _STATUS_TEXT.get(status_code, ("unknown", "unknown"))

    data = _base_status("uptimerobot", True)
    data.update(
        {
            "ok": status == "up",
            "status": status,
            "status_text": status_text,
            "uptime_7d": _uptime_ratio(monitor, 0),
            "uptime_30d": _uptime_ratio(monitor, 1),
            "response_time_ms": _latest_response_time(monitor),
        }
    )
    return data


@router.get("")
async def uptime_summary() -> dict[str, Any]:
    now = time.monotonic()
    if _CACHE["data"] is not None and now < _CACHE["until"]:
        return _CACHE["data"]

    has_provider = bool(settings.uptime_robot_api_key.strip())
    if has_provider:
        try:
            data = await _from_uptimerobot()
        except Exception:
            data = _base_status("local", True)
            data["source"] = "local-fallback"
            data["provider_note"] = "uptime provider unavailable"
    else:
        data = _base_status("local", False)

    _CACHE["data"] = data
    _CACHE["until"] = now + max(30, settings.uptime_cache_seconds)
    return data
