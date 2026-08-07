from apps.notifications.services.badge import unread_count_for_user


def notifications_badge(request):
    """Expose unread notification count for the authenticated user (sidebar badge)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"notifications_unread": 0}
    return {"notifications_unread": unread_count_for_user(user.pk)}
