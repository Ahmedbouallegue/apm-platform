from datetime import date, timedelta

from celery import shared_task
from django.utils import timezone

from apps.certificates.models import Certificate
from apps.contracts.models import Contract
from apps.domains.models import Domain
from apps.notifications.models import Notification, PlatformSettings
from apps.notifications.services.notifications import notify_managers


@shared_task
def ping() -> str:
    return "pong"


def _expiry_already_notified(*, fingerprint: str, cooldown_days: int) -> bool:
    """Avoid flooding when the daily beat re-scans the same resource+threshold."""
    since = timezone.now() - timedelta(days=cooldown_days)
    return Notification.objects.filter(
        notification_type=Notification.NotificationType.EXPIRY,
        link=fingerprint,
        sent_at__gte=since,
    ).exists()


def _matching_threshold(days_left: int, thresholds: list[int]) -> int | None:
    """Tightest threshold that still covers days_left (e.g. 10 → 30, 45 → 60)."""
    if days_left < 0:
        return 0 if 0 in thresholds else None
    for threshold in sorted(thresholds):
        if days_left <= threshold:
            return threshold
    return None


def _threshold_label(threshold: int) -> str:
    if threshold == 0:
        return "J-0 (expiration)"
    return f"J-{threshold}"


def _scan_certificates(*, today: date, thresholds: list[int], cooldown: int) -> tuple[int, int]:
    created = skipped = 0
    certs = Certificate.objects.filter(
        is_deleted=False,
        is_active=True,
        expires_at__isnull=False,
    ).exclude(status=Certificate.Status.REVOKED)

    for cert in certs:
        days_left = (cert.expires_at - today).days
        if days_left < 0:
            if cert.status != Certificate.Status.EXPIRED:
                cert.status = Certificate.Status.EXPIRED
                cert.save(update_fields=["status", "updated_at"])
        elif days_left <= max(thresholds):
            if cert.status not in {Certificate.Status.EXPIRING, Certificate.Status.EXPIRED}:
                cert.status = Certificate.Status.EXPIRING
                cert.save(update_fields=["status", "updated_at"])

        threshold = _matching_threshold(days_left, thresholds)
        if threshold is None:
            continue

        fingerprint = f"/certificates/{cert.pk}/?seuil={threshold}"
        if _expiry_already_notified(fingerprint=fingerprint, cooldown_days=cooldown):
            skipped += 1
            continue

        label = _threshold_label(threshold)
        if days_left < 0:
            title = f"Certificat SSL expiré — {cert.common_name}"
            message = f"Expiré depuis le {cert.expires_at:%d/%m/%Y} ({label})."
        elif threshold == 0:
            title = f"Certificat SSL expire aujourd’hui — {cert.common_name}"
            message = f"Expiration le {cert.expires_at:%d/%m/%Y} ({label})."
        else:
            title = f"Certificat SSL bientôt expiré — {cert.common_name}"
            message = (
                f"Expiration le {cert.expires_at:%d/%m/%Y} "
                f"(dans {days_left} j, alerte {label})."
            )
        notify_managers(
            title=title,
            message=message,
            notification_type=Notification.NotificationType.EXPIRY,
            link=fingerprint,
        )
        created += 1
    return created, skipped


def _scan_domains(*, today: date, thresholds: list[int], cooldown: int) -> tuple[int, int]:
    created = skipped = 0
    domains = Domain.objects.filter(
        is_deleted=False,
        is_active=True,
        expires_at__isnull=False,
    )

    for domain in domains:
        days_left = (domain.expires_at - today).days
        if days_left < 0:
            if domain.status != Domain.Status.EXPIRED:
                domain.status = Domain.Status.EXPIRED
                domain.save(update_fields=["status", "updated_at"])
        elif days_left <= max(thresholds):
            if domain.status != Domain.Status.EXPIRING:
                domain.status = Domain.Status.EXPIRING
                domain.save(update_fields=["status", "updated_at"])

        threshold = _matching_threshold(days_left, thresholds)
        if threshold is None:
            continue

        fingerprint = f"/domains/{domain.pk}/?seuil={threshold}"
        if _expiry_already_notified(fingerprint=fingerprint, cooldown_days=cooldown):
            skipped += 1
            continue

        label = _threshold_label(threshold)
        if days_left < 0:
            title = f"Domaine expiré — {domain.fqdn}"
            message = f"Expiré depuis le {domain.expires_at:%d/%m/%Y} ({label})."
        elif threshold == 0:
            title = f"Domaine expire aujourd’hui — {domain.fqdn}"
            message = f"Expiration le {domain.expires_at:%d/%m/%Y} ({label})."
        else:
            title = f"Domaine bientôt expiré — {domain.fqdn}"
            message = (
                f"Expiration le {domain.expires_at:%d/%m/%Y} "
                f"(dans {days_left} j, alerte {label})."
            )
        notify_managers(
            title=title,
            message=message,
            notification_type=Notification.NotificationType.EXPIRY,
            link=fingerprint,
        )
        created += 1
    return created, skipped


def _scan_contracts(*, today: date, thresholds: list[int], cooldown: int) -> tuple[int, int]:
    created = skipped = 0
    contracts = Contract.objects.filter(
        is_deleted=False,
        is_active=True,
        end_date__isnull=False,
    ).exclude(status=Contract.Status.TERMINATED)

    for contract in contracts:
        days_left = (contract.end_date - today).days
        if days_left < 0:
            if contract.status != Contract.Status.EXPIRED:
                contract.status = Contract.Status.EXPIRED
                contract.save(update_fields=["status", "updated_at"])
        elif days_left <= max(thresholds):
            if contract.status != Contract.Status.EXPIRING:
                contract.status = Contract.Status.EXPIRING
                contract.save(update_fields=["status", "updated_at"])

        threshold = _matching_threshold(days_left, thresholds)
        if threshold is None:
            continue

        fingerprint = f"/contracts/{contract.pk}/?seuil={threshold}"
        if _expiry_already_notified(fingerprint=fingerprint, cooldown_days=cooldown):
            skipped += 1
            continue

        label = _threshold_label(threshold)
        if days_left < 0:
            title = f"Contrat expiré — {contract.reference}"
            message = f"Fin le {contract.end_date:%d/%m/%Y} ({contract.title}, {label})."
        elif threshold == 0:
            title = f"Contrat expire aujourd’hui — {contract.reference}"
            message = f"Fin le {contract.end_date:%d/%m/%Y} ({contract.title}, {label})."
        else:
            title = f"Contrat bientôt expiré — {contract.reference}"
            message = (
                f"Fin le {contract.end_date:%d/%m/%Y} ({contract.title}) "
                f"— dans {days_left} j, alerte {label}."
            )
        notify_managers(
            title=title,
            message=message,
            notification_type=Notification.NotificationType.EXPIRY,
            link=fingerprint,
        )
        created += 1
    return created, skipped


@shared_task
def check_expiring_resources(days: int | None = None) -> dict:
    """
    Scan quotidien SSL / domaines / contrats.

    Seuils configurables (paramètres plateforme) : J-60, J-30, J-0 par défaut.
    Le paramètre ``days`` (legacy Beat) force le seuil max si fourni.
    """
    settings_obj = PlatformSettings.load()
    thresholds = settings_obj.thresholds()
    if days is not None:
        # Keep backward compatibility with beat args=(30,) while still
        # emitting J-0 and the configured mid threshold when relevant.
        thresholds = sorted({*thresholds, int(days)})
        if not settings_obj.alert_on_expiry and 0 in thresholds and days != 0:
            thresholds = [t for t in thresholds if t != 0] or thresholds

    cooldown = int(settings_obj.alert_cooldown_days)
    today = timezone.localdate()
    if not thresholds:
        return {"created": {}, "skipped": {}, "thresholds": []}

    c_created, c_skipped = _scan_certificates(
        today=today, thresholds=thresholds, cooldown=cooldown
    )
    d_created, d_skipped = _scan_domains(
        today=today, thresholds=thresholds, cooldown=cooldown
    )
    k_created, k_skipped = _scan_contracts(
        today=today, thresholds=thresholds, cooldown=cooldown
    )

    return {
        "created": {
            "certificates": c_created,
            "domains": d_created,
            "contracts": k_created,
        },
        "skipped": {
            "certificates": c_skipped,
            "domains": d_skipped,
            "contracts": k_skipped,
        },
        "thresholds": thresholds,
    }
