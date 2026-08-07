from django.db import transaction
from django.utils import timezone

from apps.audit.services.audit import audit_log_create
from apps.incidents.models import Incident
from apps.notifications.models import Notification
from apps.notifications.services.notifications import notify_managers


@transaction.atomic
def incident_create(*, data: dict, user=None) -> Incident:
    incident = Incident(**data)
    if user and not incident.reported_by_id:
        incident.reported_by = user
    incident.full_clean()
    incident.save()
    audit_log_create(
        action="create",
        entity="Incident",
        entity_id=incident.pk,
        details=f"Incident « {incident.title} » créé",
        user=user,
    )
    notify_managers(
        title=f"Nouvel incident — {incident.title}",
        message=f"Impact {incident.get_impact_display()} sur {incident.application.name}.",
        notification_type=Notification.NotificationType.INCIDENT,
        link=f"/incidents/{incident.pk}/",
    )
    return incident


@transaction.atomic
def incident_update(*, incident: Incident, data: dict, user=None) -> Incident:
    for field, value in data.items():
        setattr(incident, field, value)
    incident.full_clean()
    incident.save()
    audit_log_create(
        action="update",
        entity="Incident",
        entity_id=incident.pk,
        details=f"Incident « {incident.title} » mis à jour",
        user=user,
    )
    return incident


@transaction.atomic
def incident_soft_delete(*, incident: Incident, user=None) -> Incident:
    incident.is_deleted = True
    incident.deleted_at = timezone.now()
    incident.status = Incident.Status.CLOSED
    incident.save(update_fields=["is_deleted", "deleted_at", "status", "updated_at"])
    audit_log_create(
        action="delete",
        entity="Incident",
        entity_id=incident.pk,
        details=f"Incident « {incident.title} » archivé",
        user=user,
    )
    return incident
