from django.db import transaction

from apps.technologies.models import Technology


@transaction.atomic
def technology_create(*, data: dict) -> Technology:
    tech = Technology(**data)
    tech.full_clean()
    tech.save()
    return tech


@transaction.atomic
def technology_update(*, technology: Technology, data: dict) -> Technology:
    for field, value in data.items():
        setattr(technology, field, value)
    technology.full_clean()
    technology.save()
    return technology


@transaction.atomic
def technology_delete(*, technology: Technology) -> None:
    technology.delete()
