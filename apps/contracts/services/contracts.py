from django.db import transaction
from django.utils import timezone

from apps.audit.services.audit import audit_log_create
from apps.contracts.models import Contract
from apps.dashboard.selectors.dashboard import invalidate_dashboard_stats


@transaction.atomic
def contract_create(*, data: dict, user=None) -> Contract:
    contract = Contract(**data)
    contract.full_clean()
    contract.save()
    audit_log_create(
        action="create",
        entity="Contract",
        entity_id=contract.pk,
        details=f"Contrat « {contract.reference} » créé",
        user=user,
    )
    invalidate_dashboard_stats()
    return contract


@transaction.atomic
def contract_update(*, contract: Contract, data: dict, user=None) -> Contract:
    for field, value in data.items():
        setattr(contract, field, value)
    contract.full_clean()
    contract.save()
    audit_log_create(
        action="update",
        entity="Contract",
        entity_id=contract.pk,
        details=f"Contrat « {contract.reference} » mis à jour",
        user=user,
    )
    invalidate_dashboard_stats()
    return contract


@transaction.atomic
def contract_soft_delete(*, contract: Contract, user=None) -> Contract:
    contract.is_deleted = True
    contract.deleted_at = timezone.now()
    contract.is_active = False
    contract.status = Contract.Status.TERMINATED
    contract.save(
        update_fields=["is_deleted", "deleted_at", "is_active", "status", "updated_at"]
    )
    audit_log_create(
        action="delete",
        entity="Contract",
        entity_id=contract.pk,
        details=f"Contrat « {contract.reference} » archivé",
        user=user,
    )
    invalidate_dashboard_stats()
    return contract
