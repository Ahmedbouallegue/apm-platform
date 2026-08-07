from django.db.models import Q, QuerySet

from apps.audit.models import AuditLog


def audit_log_list(
    *,
    search: str | None = None,
    action: str | None = None,
    entity: str | None = None,
    user_id: int | None = None,
) -> QuerySet[AuditLog]:
    qs = AuditLog.objects.select_related("user")
    if search:
        qs = qs.filter(
            Q(action__icontains=search)
            | Q(entity__icontains=search)
            | Q(entity_id__icontains=search)
            | Q(details__icontains=search)
            | Q(user__username__icontains=search)
        )
    if action:
        qs = qs.filter(action=action)
    if entity:
        qs = qs.filter(entity=entity)
    if user_id:
        qs = qs.filter(user_id=user_id)
    return qs.order_by("-occurred_at")
