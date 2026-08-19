"""Rate limiting léger basé cache (login, JWT, reset password)."""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or "unknown"


def rate_limit_key(request, *, scope: str) -> str:
    return f"rate_limit:{scope}:{_client_ip(request)}"


def is_rate_limited(request, *, scope: str) -> bool:
    if not getattr(settings, "LOGIN_RATE_LIMIT_ENABLED", True):
        return False
    key = rate_limit_key(request, scope=scope)
    attempts = cache.get(key, 0)
    return attempts >= int(getattr(settings, "LOGIN_RATE_LIMIT_MAX_ATTEMPTS", 10))


def register_rate_limit_attempt(request, *, scope: str) -> int:
    key = rate_limit_key(request, scope=scope)
    window = int(getattr(settings, "LOGIN_RATE_LIMIT_WINDOW_SECONDS", 300))
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, timeout=window)
    return attempts


def clear_rate_limit(request, *, scope: str) -> None:
    cache.delete(rate_limit_key(request, scope=scope))
