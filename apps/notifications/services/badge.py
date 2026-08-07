"""Cache helpers for the sidebar unread notification badge."""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache

from apps.notifications.models import Notification

UNREAD_BADGE_CACHE_PREFIX = "notif:unread:"


def _unread_cache_key(user_id: int) -> str:
    return f"{UNREAD_BADGE_CACHE_PREFIX}{user_id}"


def unread_count_for_user(user_id: int) -> int:
    ttl = int(getattr(settings, "NOTIFICATION_BADGE_CACHE_TTL", 60))
    key = _unread_cache_key(user_id)
    if ttl > 0:
        cached = cache.get(key)
        if cached is not None:
            return int(cached)

    count = Notification.objects.filter(
        user_id=user_id,
        status=Notification.Status.UNREAD,
    ).count()

    if ttl > 0:
        cache.set(key, count, ttl)
    return count


def invalidate_unread_badge(user_id: int | None) -> None:
    if user_id is None:
        return
    cache.delete(_unread_cache_key(user_id))
