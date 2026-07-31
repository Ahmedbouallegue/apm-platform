from django.db import transaction
from django.utils import timezone

from apps.applications.models import Application


@transaction.atomic
def application_create(*, data: dict, technology_ids: list[int] | None = None) -> Application:
    technologies = data.pop("technologies", None)
    app = Application(**data)
    app.full_clean()
    app.save()
    ids = technology_ids if technology_ids is not None else technologies
    if ids is not None:
        app.technologies.set(ids)
    return app


@transaction.atomic
def application_update(
    *,
    application: Application,
    data: dict,
    technology_ids: list[int] | None = None,
) -> Application:
    technologies = data.pop("technologies", None)
    for field, value in data.items():
        setattr(application, field, value)
    application.full_clean()
    application.save()
    ids = technology_ids if technology_ids is not None else technologies
    if ids is not None:
        application.technologies.set(ids)
    return application


@transaction.atomic
def application_soft_delete(*, application: Application) -> Application:
    application.is_deleted = True
    application.deleted_at = timezone.now()
    application.status = Application.Status.RETIRED
    application.save(update_fields=["is_deleted", "deleted_at", "status", "updated_at"])
    return application


@transaction.atomic
def application_restore(*, application: Application) -> Application:
    application.is_deleted = False
    application.deleted_at = None
    application.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
    return application
