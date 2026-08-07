from datetime import date, timedelta

from celery import shared_task
from django.utils import timezone

from apps.certificates.models import Certificate
from apps.contracts.models import Contract
from apps.dashboard.selectors.dashboard import invalidate_dashboard_stats
from apps.domains.models import Domain
from apps.notifications.models import Notification, PlatformSettings
from apps.notifications.services.notifications import notify_managers


@shared_task
def ping() -> str:
    return "pong"


def _recent_expiry_fingerprints(*, cooldown_days: int) -> set[str]:
    """One query for all recent expiry notifications (avoids N× exists)."""
    since = timezone.now() - timedelta(days=cooldown_days)
    return set(
        Notification.objects.filter(
            notification_type=Notification.NotificationType.EXPIRY,
            sent_at__gte=since,
        )
        .exclude(link="")
        .values_list("link", flat=True)
        .distinct()
    )


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


def _scan_certificates(
    *,
    today: date,
    thresholds: list[int],
    notified: set[str],
) -> tuple[int, int]:
    created = skipped = 0
    horizon = today + timedelta(days=max(thresholds))
    certs = list(
        Certificate.objects.filter(
            is_deleted=False,
            is_active=True,
            expires_at__isnull=False,
            expires_at__lte=horizon,
        ).exclude(status=Certificate.Status.REVOKED)
    )

    status_updates: list[Certificate] = []
    for cert in certs:
        days_left = (cert.expires_at - today).days
        new_status = None
        if days_left < 0 and cert.status != Certificate.Status.EXPIRED:
            new_status = Certificate.Status.EXPIRED
        elif (
            days_left >= 0
            and days_left <= max(thresholds)
            and cert.status not in {Certificate.Status.EXPIRING, Certificate.Status.EXPIRED}
        ):
            new_status = Certificate.Status.EXPIRING
        if new_status is not None:
            cert.status = new_status
            status_updates.append(cert)

        threshold = _matching_threshold(days_left, thresholds)
        if threshold is None:
            continue

        fingerprint = f"/certificates/{cert.pk}/?seuil={threshold}"
        if fingerprint in notified:
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
        notified.add(fingerprint)
        created += 1

    if status_updates:
        Certificate.objects.bulk_update(status_updates, ["status", "updated_at"])
    return created, skipped


def _scan_domains(
    *,
    today: date,
    thresholds: list[int],
    notified: set[str],
) -> tuple[int, int]:
    created = skipped = 0
    horizon = today + timedelta(days=max(thresholds))
    domains = list(
        Domain.objects.filter(
            is_deleted=False,
            is_active=True,
            expires_at__isnull=False,
            expires_at__lte=horizon,
        )
    )

    status_updates: list[Domain] = []
    for domain in domains:
        days_left = (domain.expires_at - today).days
        new_status = None
        if days_left < 0 and domain.status != Domain.Status.EXPIRED:
            new_status = Domain.Status.EXPIRED
        elif days_left >= 0 and days_left <= max(thresholds) and domain.status != Domain.Status.EXPIRING:
            new_status = Domain.Status.EXPIRING
        if new_status is not None:
            domain.status = new_status
            status_updates.append(domain)

        threshold = _matching_threshold(days_left, thresholds)
        if threshold is None:
            continue

        fingerprint = f"/domains/{domain.pk}/?seuil={threshold}"
        if fingerprint in notified:
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
        notified.add(fingerprint)
        created += 1

    if status_updates:
        Domain.objects.bulk_update(status_updates, ["status", "updated_at"])
    return created, skipped


def _scan_contracts(
    *,
    today: date,
    thresholds: list[int],
    notified: set[str],
) -> tuple[int, int]:
    created = skipped = 0
    horizon = today + timedelta(days=max(thresholds))
    contracts = list(
        Contract.objects.filter(
            is_deleted=False,
            is_active=True,
            end_date__isnull=False,
            end_date__lte=horizon,
        ).exclude(status=Contract.Status.TERMINATED)
    )

    status_updates: list[Contract] = []
    for contract in contracts:
        days_left = (contract.end_date - today).days
        new_status = None
        if days_left < 0 and contract.status != Contract.Status.EXPIRED:
            new_status = Contract.Status.EXPIRED
        elif (
            days_left >= 0
            and days_left <= max(thresholds)
            and contract.status != Contract.Status.EXPIRING
        ):
            new_status = Contract.Status.EXPIRING
        if new_status is not None:
            contract.status = new_status
            status_updates.append(contract)

        threshold = _matching_threshold(days_left, thresholds)
        if threshold is None:
            continue

        fingerprint = f"/contracts/{contract.pk}/?seuil={threshold}"
        if fingerprint in notified:
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
        notified.add(fingerprint)
        created += 1

    if status_updates:
        Contract.objects.bulk_update(status_updates, ["status", "updated_at"])
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

    notified = _recent_expiry_fingerprints(cooldown_days=cooldown)
    c_created, c_skipped = _scan_certificates(
        today=today, thresholds=thresholds, notified=notified
    )
    d_created, d_skipped = _scan_domains(
        today=today, thresholds=thresholds, notified=notified
    )
    k_created, k_skipped = _scan_contracts(
        today=today, thresholds=thresholds, notified=notified
    )

    if c_created or d_created or k_created or c_skipped or d_skipped or k_skipped:
        invalidate_dashboard_stats()

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
