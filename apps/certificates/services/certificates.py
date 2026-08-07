from django.db import transaction
from django.utils import timezone

from apps.audit.services.audit import audit_log_create
from apps.certificates.models import Certificate


@transaction.atomic
def certificate_create(*, data: dict, user=None) -> Certificate:
    cert = Certificate(**data)
    cert.full_clean()
    cert.save()
    audit_log_create(
        action="create",
        entity="Certificate",
        entity_id=cert.pk,
        details=f"Certificat SSL « {cert.common_name} » créé",
        user=user,
    )
    return cert


@transaction.atomic
def certificate_update(*, certificate: Certificate, data: dict, user=None) -> Certificate:
    for field, value in data.items():
        setattr(certificate, field, value)
    certificate.full_clean()
    certificate.save()
    audit_log_create(
        action="update",
        entity="Certificate",
        entity_id=certificate.pk,
        details=f"Certificat SSL « {certificate.common_name} » mis à jour",
        user=user,
    )
    return certificate


@transaction.atomic
def certificate_soft_delete(*, certificate: Certificate, user=None) -> Certificate:
    certificate.is_deleted = True
    certificate.deleted_at = timezone.now()
    certificate.is_active = False
    certificate.status = Certificate.Status.REVOKED
    certificate.save(
        update_fields=["is_deleted", "deleted_at", "is_active", "status", "updated_at"]
    )
    audit_log_create(
        action="delete",
        entity="Certificate",
        entity_id=certificate.pk,
        details=f"Certificat SSL « {certificate.common_name} » archivé",
        user=user,
    )
    return certificate
