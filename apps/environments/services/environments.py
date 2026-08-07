from django.db import transaction

from apps.audit.services.audit import audit_log_create
from apps.environments.models import Environment


@transaction.atomic
def environment_create(*, data: dict, user=None) -> Environment:
    env = Environment(**data)
    env.full_clean()
    env.save()
    audit_log_create(
        action="create",
        entity="Environment",
        entity_id=env.pk,
        details=f"Environnement « {env} » créé",
        user=user,
    )
    return env


@transaction.atomic
def environment_update(*, environment: Environment, data: dict, user=None) -> Environment:
    for field, value in data.items():
        setattr(environment, field, value)
    environment.full_clean()
    environment.save()
    audit_log_create(
        action="update",
        entity="Environment",
        entity_id=environment.pk,
        details=f"Environnement « {environment} » mis à jour",
        user=user,
    )
    return environment


@transaction.atomic
def environment_delete(*, environment: Environment, user=None) -> None:
    label = str(environment)
    pk = environment.pk
    environment.delete()
    audit_log_create(
        action="delete",
        entity="Environment",
        entity_id=pk,
        details=f"Environnement « {label} » supprimé",
        user=user,
    )
