from django.db.models import Q, QuerySet

from apps.notifications.models import Notification


def notification_list(
    *,
    user=None,
    status: str | None = None,
    notification_type: str | None = None,
    search: str | None = None,
) -> QuerySet[Notification]:
    qs = Notification.objects.select_related("user")
    if user is not None:
        qs = qs.filter(user=user)
    if status:
        qs = qs.filter(status=status)
    if notification_type:
        qs = qs.filter(notification_type=notification_type)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(message__icontains=search))
    return qs.order_by("-sent_at")
