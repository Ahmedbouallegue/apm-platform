from django.db.models import Case, IntegerField, Value, When

from apps.notifications.models import Notification
from apps.notifications.services.badge import unread_count_for_user


def notifications_badge(request):
    """Expose unread count + recent titles for the topbar dropdown."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {
            "notifications_unread": 0,
            "notifications_preview": [],
        }

    unread_first = Case(
        When(status=Notification.Status.UNREAD, then=Value(0)),
        default=Value(1),
        output_field=IntegerField(),
    )
    preview = list(
        Notification.objects.filter(user=user)
        .exclude(status=Notification.Status.ARCHIVED)
        .order_by(unread_first, "-sent_at")
        .only("id", "title", "status", "link", "sent_at", "notification_type")[:8]
    )
    return {
        "notifications_unread": unread_count_for_user(user.pk),
        "notifications_preview": preview,
    }
