from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog


@transaction.atomic
def audit_log_create(
    *,
    action: str,
    entity: str,
    entity_id: str = "",
    details: str = "",
    user=None,
    ip_address=None,
) -> AuditLog:
    return AuditLog.objects.create(
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id is not None else "",
        details=details,
        user=user,
        ip_address=ip_address,
    )
