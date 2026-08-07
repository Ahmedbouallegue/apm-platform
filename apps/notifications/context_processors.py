from apps.notifications.models import Notification


def notifications_badge(request):
    """Expose unread notification count for the authenticated user (sidebar badge)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"notifications_unread": 0}
    count = Notification.objects.filter(
        user=user,
        status=Notification.Status.UNREAD,
    ).count()
    return {"notifications_unread": count}
