from django.db import transaction
from django.utils import timezone

from apps.applications.models import Application
from apps.audit.services.audit import audit_log_create
from apps.dashboard.selectors.dashboard import invalidate_dashboard_stats


@transaction.atomic
def application_create(
    *,
    data: dict,
    technology_ids: list[int] | None = None,
    user=None,
) -> Application:
    technologies = data.pop("technologies", None)
    app = Application(**data)
    app.full_clean()
    app.save()
    ids = technology_ids if technology_ids is not None else technologies
    if ids is not None:
        app.technologies.set(ids)
    audit_log_create(
        action="create",
        entity="Application",
        entity_id=app.pk,
        details=f"Application « {app.name} » créée",
        user=user,
    )
    invalidate_dashboard_stats()
    return app


@transaction.atomic
def application_update(
    *,
    application: Application,
    data: dict,
    technology_ids: list[int] | None = None,
    user=None,
) -> Application:
    technologies = data.pop("technologies", None)
    for field, value in data.items():
        setattr(application, field, value)
    application.full_clean()
    application.save()
    ids = technology_ids if technology_ids is not None else technologies
    if ids is not None:
        application.technologies.set(ids)
    audit_log_create(
        action="update",
        entity="Application",
        entity_id=application.pk,
        details=f"Application « {application.name} » mise à jour",
        user=user,
    )
    invalidate_dashboard_stats()
    return application


@transaction.atomic
def application_soft_delete(*, application: Application, user=None) -> Application:
    application.is_deleted = True
    application.deleted_at = timezone.now()
    application.status = Application.Status.RETIRED
    application.save(update_fields=["is_deleted", "deleted_at", "status", "updated_at"])
    audit_log_create(
        action="delete",
        entity="Application",
        entity_id=application.pk,
        details=f"Application « {application.name} » archivée",
        user=user,
    )
    invalidate_dashboard_stats()
    return application


@transaction.atomic
def application_restore(*, application: Application, user=None) -> Application:
    application.is_deleted = False
    application.deleted_at = None
    application.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
    audit_log_create(
        action="restore",
        entity="Application",
        entity_id=application.pk,
        details=f"Application « {application.name} » restaurée",
        user=user,
    )
    invalidate_dashboard_stats()
    return application
