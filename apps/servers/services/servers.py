from django.db import transaction
from django.utils import timezone

from apps.audit.services.audit import audit_log_create
from apps.servers.models import Server


@transaction.atomic
def server_create(*, data: dict, user=None) -> Server:
    server = Server(**data)
    server.full_clean()
    server.save()
    audit_log_create(
        action="create",
        entity="Server",
        entity_id=server.pk,
        details=f"Serveur « {server.name} » créé",
        user=user,
    )
    return server


@transaction.atomic
def server_update(*, server: Server, data: dict, user=None) -> Server:
    for field, value in data.items():
        setattr(server, field, value)
    server.full_clean()
    server.save()
    audit_log_create(
        action="update",
        entity="Server",
        entity_id=server.pk,
        details=f"Serveur « {server.name} » mis à jour",
        user=user,
    )
    return server


@transaction.atomic
def server_soft_delete(*, server: Server, user=None) -> Server:
    server.is_deleted = True
    server.deleted_at = timezone.now()
    server.is_active = False
    server.save(update_fields=["is_deleted", "deleted_at", "is_active", "updated_at"])
    audit_log_create(
        action="delete",
        entity="Server",
        entity_id=server.pk,
        details=f"Serveur « {server.name} » archivé",
        user=user,
    )
    return server
