from django.db import transaction
from django.utils import timezone

from apps.servers.models import Server


@transaction.atomic
def server_create(*, data: dict) -> Server:
    server = Server(**data)
    server.full_clean()
    server.save()
    return server


@transaction.atomic
def server_update(*, server: Server, data: dict) -> Server:
    for field, value in data.items():
        setattr(server, field, value)
    server.full_clean()
    server.save()
    return server


@transaction.atomic
def server_soft_delete(*, server: Server) -> Server:
    server.is_deleted = True
    server.deleted_at = timezone.now()
    server.is_active = False
    server.save(update_fields=["is_deleted", "deleted_at", "is_active", "updated_at"])
    return server
