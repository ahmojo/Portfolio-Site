"""Privacy-preserving request metadata helpers for first-party analytics."""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
from datetime import date
from urllib.parse import urlsplit


def _valid_ip(value: str) -> str:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return ""


def _is_trusted_proxy(peer_ip: str, trusted_proxy_cidrs: list[str]) -> bool:
    try:
        peer = ipaddress.ip_address(peer_ip)
    except ValueError:
        return False
    for cidr in trusted_proxy_cidrs:
        try:
            if peer in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


def resolve_client_ip(
    peer_ip: str,
    cf_connecting_ip: str,
    x_forwarded_for: str,
    trusted_proxy_cidrs: list[str],
) -> str:
    """Use forwarding headers only when the direct network peer is trusted."""
    peer = _valid_ip(peer_ip)
    if not peer or not _is_trusted_proxy(peer, trusted_proxy_cidrs):
        return peer

    cloudflare_ip = _valid_ip(cf_connecting_ip)
    if cloudflare_ip:
        return cloudflare_ip

    forwarded_ip = _valid_ip(x_forwarded_for.split(",", 1)[0])
    return forwarded_ip or peer


def referrer_hostname(value: str) -> str:
    """Keep only a normalized hostname; discard paths, queries, and fragments."""
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"}:
        return ""
    try:
        return (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def daily_visitor_hash(ip: str, secret: str, day: date | None = None) -> str:
    """Return a one-day pseudonymous token that cannot reveal the source IP."""
    if not ip or not secret:
        return ""
    bucket = (day or date.today()).isoformat()
    message = f"{bucket}\0{ip}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()[:32]
