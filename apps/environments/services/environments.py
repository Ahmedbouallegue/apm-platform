from django.db import transaction

from apps.environments.models import Environment


@transaction.atomic
def environment_create(*, data: dict) -> Environment:
    env = Environment(**data)
    env.full_clean()
    env.save()
    return env


@transaction.atomic
def environment_update(*, environment: Environment, data: dict) -> Environment:
    for field, value in data.items():
        setattr(environment, field, value)
    environment.full_clean()
    environment.save()
    return environment


@transaction.atomic
def environment_delete(*, environment: Environment) -> None:
    environment.delete()
