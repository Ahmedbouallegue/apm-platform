from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.accounts.roles import WRITE_ROLES
from apps.notifications.models import Notification
from apps.notifications.services.badge import invalidate_unread_badge

User = get_user_model()


@transaction.atomic
def notification_create(*, data: dict) -> Notification:
    notification = Notification(**data)
    notification.full_clean()
    notification.save()
    invalidate_unread_badge(notification.user_id)
    return notification


@transaction.atomic
def notification_mark_read(*, notification: Notification) -> Notification:
    notification.status = Notification.Status.READ
    notification.save(update_fields=["status", "updated_at"])
    invalidate_unread_badge(notification.user_id)
    return notification


@transaction.atomic
def notification_archive(*, notification: Notification) -> Notification:
    notification.status = Notification.Status.ARCHIVED
    notification.save(update_fields=["status", "updated_at"])
    invalidate_unread_badge(notification.user_id)
    return notification


def notify_users(
    *,
    users,
    title: str,
    message: str,
    notification_type: str = Notification.NotificationType.INFO,
    link: str = "",
) -> int:
    user_list = list(users)
    if not user_list:
        return 0

    now = timezone.now()
    rows = [
        Notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
            status=Notification.Status.UNREAD,
            sent_at=now,
            created_at=now,
            updated_at=now,
        )
        for user in user_list
    ]
    Notification.objects.bulk_create(rows)
    for user in user_list:
        invalidate_unread_badge(user.pk)
    return len(rows)


def notify_managers(
    *,
    title: str,
    message: str,
    notification_type: str = Notification.NotificationType.ALERT,
    link: str = "",
) -> int:
    users = User.objects.filter(
        is_active=True,
        role__in=WRITE_ROLES,
    )
    return notify_users(
        users=users,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )


def notify_user_login(*, user, method: str = "password") -> Notification | None:
    """
    Create at most one system login notification per user per calendar day.
    Returns the notification if created, otherwise None.
    """
    today = timezone.localdate()
    already = Notification.objects.filter(
        user=user,
        notification_type=Notification.NotificationType.SYSTEM,
        title__startswith="Connexion",
        sent_at__date=today,
    ).exists()
    if already:
        return None

    method_label = "reconnaissance faciale" if method == "face" else "mot de passe"
    display = user.get_full_name() or user.get_username()
    return notification_create(
        data={
            "user": user,
            "title": "Connexion réussie",
            "message": (
                f"Bonjour {display}. Connexion à Topnet APM via {method_label} "
                f"le {timezone.localtime():%d/%m/%Y à %H:%M}."
            ),
            "notification_type": Notification.NotificationType.SYSTEM,
            "status": Notification.Status.UNREAD,
            "link": "/notifications/",
        }
    )