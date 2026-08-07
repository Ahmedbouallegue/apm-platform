from django.db import transaction
from django.utils import timezone

from apps.audit.services.audit import audit_log_create
from apps.domains.models import Domain


@transaction.atomic
def domain_create(*, data: dict, user=None) -> Domain:
    domain = Domain(**data)
    domain.full_clean()
    domain.save()
    audit_log_create(
        action="create",
        entity="Domain",
        entity_id=domain.pk,
        details=f"Domaine « {domain.fqdn} » créé",
        user=user,
    )
    return domain


@transaction.atomic
def domain_update(*, domain: Domain, data: dict, user=None) -> Domain:
    for field, value in data.items():
        setattr(domain, field, value)
    domain.full_clean()
    domain.save()
    audit_log_create(
        action="update",
        entity="Domain",
        entity_id=domain.pk,
        details=f"Domaine « {domain.fqdn} » mis à jour",
        user=user,
    )
    return domain


@transaction.atomic
def domain_soft_delete(*, domain: Domain, user=None) -> Domain:
    domain.is_deleted = True
    domain.deleted_at = timezone.now()
    domain.is_active = False
    domain.status = Domain.Status.EXPIRED
    domain.save(
        update_fields=["is_deleted", "deleted_at", "is_active", "status", "updated_at"]
    )
    audit_log_create(
        action="delete",
        entity="Domain",
        entity_id=domain.pk,
        details=f"Domaine « {domain.fqdn} » archivé",
        user=user,
    )
    return domain
