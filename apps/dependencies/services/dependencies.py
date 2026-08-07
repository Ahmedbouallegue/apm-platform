from django.db import transaction
from django.utils import timezone

from apps.audit.services.audit import audit_log_create
from apps.dependencies.models import Dependency


@transaction.atomic
def dependency_create(*, data: dict, user=None) -> Dependency:
    dependency = Dependency(**data)
    dependency.full_clean()
    dependency.save()
    audit_log_create(
        action="create",
        entity="Dependency",
        entity_id=dependency.pk,
        details=str(dependency),
        user=user,
    )
    return dependency


@transaction.atomic
def dependency_update(*, dependency: Dependency, data: dict, user=None) -> Dependency:
    for field, value in data.items():
        setattr(dependency, field, value)
    dependency.full_clean()
    dependency.save()
    audit_log_create(
        action="update",
        entity="Dependency",
        entity_id=dependency.pk,
        details=str(dependency),
        user=user,
    )
    return dependency


@transaction.atomic
def dependency_soft_delete(*, dependency: Dependency, user=None) -> Dependency:
    dependency.is_deleted = True
    dependency.deleted_at = timezone.now()
    dependency.is_active = False
    dependency.save(update_fields=["is_deleted", "deleted_at", "is_active", "updated_at"])
    audit_log_create(
        action="delete",
        entity="Dependency",
        entity_id=dependency.pk,
        details=str(dependency),
        user=user,
    )
    return dependency
