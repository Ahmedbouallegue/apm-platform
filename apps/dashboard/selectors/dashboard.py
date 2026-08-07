from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta

from django.db.models import Count, QuerySet
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.applications.models import Application
from apps.certificates.models import Certificate
from apps.contracts.models import Contract
from apps.dependencies.models import Dependency
from apps.documents.models import Document
from apps.domains.models import Domain
from apps.incidents.models import Incident
from apps.notifications.models import Notification
from apps.technologies.models import Technology
from apps.vendors.models import Vendor

_FR_MONTHS = {
    1: "Jan",
    2: "Fév",
    3: "Mar",
    4: "Avr",
    5: "Mai",
    6: "Juin",
    7: "Juil",
    8: "Aoû",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Déc",
}


def _choice_counts(
    qs: QuerySet,
    field: str,
    choices: Sequence[tuple[str, str]],
) -> dict[str, list]:
    """Stable FR labels including zero-count categories."""
    raw = {row[field]: row["count"] for row in qs.values(field).annotate(count=Count("id"))}
    labels: list[str] = []
    values: list[int] = []
    keys: list[str] = []
    for key, label in choices:
        keys.append(key)
        labels.append(str(label))
        values.append(int(raw.get(key, 0)))
    return {"keys": keys, "labels": labels, "values": values}


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _add_months(d: date, months: int) -> date:
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    return date(year, month, 1)


def _trend_last_n_months(qs: QuerySet, *, date_field: str = "created_at", months: int = 6) -> dict:
    today = timezone.localdate()
    start = _add_months(_month_start(today), -(months - 1))
    filter_kwargs = {f"{date_field}__date__gte": start}
    rows = (
        qs.filter(**filter_kwargs)
        .annotate(month=TruncMonth(date_field))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    by_month = {}
    for row in rows:
        month = row["month"]
        if month is None:
            continue
        key = month.date() if hasattr(month, "date") else month
        by_month[_month_start(key)] = int(row["count"])

    labels: list[str] = []
    values: list[int] = []
    cursor = start
    for _ in range(months):
        labels.append(f"{_FR_MONTHS[cursor.month]} {cursor.year}")
        values.append(by_month.get(cursor, 0))
        cursor = _add_months(cursor, 1)
    return {"labels": labels, "values": values}


def _certs_expiry_buckets(certs: QuerySet, today: date) -> dict:
    expired = certs.filter(expires_at__lt=today).count()
    within_30 = certs.filter(expires_at__gte=today, expires_at__lte=today + timedelta(days=30)).count()
    within_90 = certs.filter(
        expires_at__gt=today + timedelta(days=30),
        expires_at__lte=today + timedelta(days=90),
    ).count()
    later = certs.filter(expires_at__gt=today + timedelta(days=90)).count()
    return {
        "labels": ["Expirés", "≤ 30 jours", "31–90 jours", "> 90 jours"],
        "values": [expired, within_30, within_90, later],
        "keys": ["expired", "d30", "d90", "later"],
    }


def _pct(part: int, total: int) -> int:
    if total <= 0:
        return 0
    return int(round(100 * part / total))


def _health_score(
    *,
    incidents_open: int,
    incidents_critical: int,
    certs_expiring: int,
    certs_expired: int,
    domains_expiring: int,
    contracts_expiring: int,
) -> dict:
    score = 100
    score -= min(40, incidents_critical * 15)
    score -= min(24, max(0, incidents_open - incidents_critical) * 6)
    score -= min(20, certs_expired * 10)
    score -= min(15, certs_expiring * 4)
    score -= min(10, domains_expiring * 3)
    score -= min(10, contracts_expiring * 3)
    score = max(0, min(100, score))
    if score >= 80:
        level, label = "ok", "Sain"
    elif score >= 55:
        level, label = "warn", "Sous surveillance"
    else:
        level, label = "critical", "Attention requise"
    return {"score": score, "level": level, "label": label}


def _upcoming_expiries(*, today: date, limit: int = 8) -> list[dict]:
    horizon = today + timedelta(days=60)
    items: list[dict] = []

    for cert in Certificate.objects.filter(
        is_deleted=False,
        is_active=True,
        expires_at__gte=today,
        expires_at__lte=horizon,
    ).exclude(status=Certificate.Status.REVOKED).order_by("expires_at")[:limit]:
        items.append(
            {
                "kind": "Certificat SSL",
                "kind_key": "cert",
                "name": cert.common_name,
                "date": cert.expires_at,
                "days_left": (cert.expires_at - today).days,
                "url": f"/certificates/{cert.pk}/",
            }
        )

    for domain in Domain.objects.filter(
        is_deleted=False,
        is_active=True,
        expires_at__isnull=False,
        expires_at__gte=today,
        expires_at__lte=horizon,
    ).order_by("expires_at")[:limit]:
        items.append(
            {
                "kind": "Domaine",
                "kind_key": "domain",
                "name": domain.fqdn,
                "date": domain.expires_at,
                "days_left": (domain.expires_at - today).days,
                "url": f"/domains/{domain.pk}/",
            }
        )

    for contract in Contract.objects.filter(
        is_deleted=False,
        is_active=True,
        end_date__gte=today,
        end_date__lte=horizon,
    ).exclude(status=Contract.Status.TERMINATED).order_by("end_date")[:limit]:
        items.append(
            {
                "kind": "Contrat",
                "kind_key": "contract",
                "name": contract.reference,
                "date": contract.end_date,
                "days_left": (contract.end_date - today).days,
                "url": f"/contracts/{contract.pk}/",
            }
        )

    items.sort(key=lambda row: (row["date"], row["name"]))
    return items[:limit]


def dashboard_stats(*, user=None) -> dict:
    today = timezone.localdate()
    soon = today + timedelta(days=30)

    from django.contrib.auth import get_user_model

    from apps.environments.models import Environment
    from apps.servers.models import Server

    User = get_user_model()

    apps_qs = Application.objects.filter(is_deleted=False)
    open_incidents = Incident.objects.filter(
        is_deleted=False,
        status__in=[Incident.Status.OPEN, Incident.Status.IN_PROGRESS],
    )
    incidents_qs = Incident.objects.filter(is_deleted=False)
    certs = Certificate.objects.filter(is_deleted=False, is_active=True)
    domains = Domain.objects.filter(is_deleted=False, is_active=True)
    contracts = Contract.objects.filter(is_deleted=False, is_active=True)
    docs_qs = Document.objects.filter(is_deleted=False)
    contracts_all = Contract.objects.filter(is_deleted=False)

    apps_total = apps_qs.count()
    apps_production = apps_qs.filter(status=Application.Status.PRODUCTION).count()
    apps_critical = apps_qs.filter(
        criticality__in=[Application.Criticality.CRITICAL, Application.Criticality.HIGH]
    ).count()
    techs_total = Technology.objects.count()
    certs_total = certs.count()
    domains_total = domains.count()
    contracts_total = contracts.count()
    vendors_total = Vendor.objects.filter(is_deleted=False).count()
    documents_total = docs_qs.count()
    dependencies_total = Dependency.objects.filter(is_deleted=False).count()
    servers_total = Server.objects.filter(is_deleted=False).count()
    envs_total = Environment.objects.count()

    certs_expiring = certs.filter(
        expires_at__lte=soon,
        expires_at__gte=today,
        status__in=[Certificate.Status.VALID, Certificate.Status.EXPIRING],
    ).count()
    certs_expired = certs.filter(expires_at__lt=today).count()
    certs_valid = certs.filter(
        status=Certificate.Status.VALID,
        expires_at__gt=soon,
    ).count()
    domains_expiring = domains.filter(
        expires_at__isnull=False,
        expires_at__lte=soon,
        expires_at__gte=today,
    ).count()
    contracts_expiring = contracts.filter(
        end_date__lte=soon,
        end_date__gte=today,
        status__in=[Contract.Status.ACTIVE, Contract.Status.EXPIRING],
    ).count()
    incidents_open = open_incidents.count()
    incidents_critical = open_incidents.filter(impact=Incident.Impact.CRITICAL).count()
    expiry_pressure = certs_expiring + domains_expiring + contracts_expiring

    unread = 0
    if user is not None and user.is_authenticated:
        unread = Notification.objects.filter(
            user=user, status=Notification.Status.UNREAD
        ).count()

    documents_by_category = list(
        docs_qs.values("category").annotate(count=Count("id")).order_by("category")
    )
    incidents_by_status = list(
        incidents_qs.values("status").annotate(count=Count("id")).order_by("status")
    )
    apps_by_criticality = list(
        apps_qs.values("criticality").annotate(count=Count("id")).order_by("criticality")
    )

    apps_by_status_chart = _choice_counts(apps_qs, "status", Application.Status.choices)
    certs_buckets = _certs_expiry_buckets(certs, today)

    charts = {
        "apps_by_status": apps_by_status_chart,
        "apps_by_criticality": _choice_counts(
            apps_qs, "criticality", Application.Criticality.choices
        ),
        "incidents_by_status": _choice_counts(
            incidents_qs, "status", Incident.Status.choices
        ),
        "incidents_by_impact": _choice_counts(
            incidents_qs, "impact", Incident.Impact.choices
        ),
        "documents_by_category": _choice_counts(
            docs_qs, "category", Document.Category.choices
        ),
        "certs_expiry_buckets": certs_buckets,
        "contracts_by_status": _choice_counts(
            contracts_all, "status", Contract.Status.choices
        ),
        "portfolio_overview": {
            "labels": [
                "Applications",
                "Technologies",
                "Certificats",
                "Domaines",
                "Contrats",
                "Fournisseurs",
                "Documents",
                "Dépendances",
            ],
            "values": [
                apps_total,
                techs_total,
                certs_total,
                domains_total,
                contracts_total,
                vendors_total,
                documents_total,
                dependencies_total,
            ],
            "keys": [
                "apps",
                "techs",
                "certs",
                "domains",
                "contracts",
                "vendors",
                "documents",
                "dependencies",
            ],
        },
        "incidents_trend_6m": _trend_last_n_months(incidents_qs, months=6),
        "apps_trend_6m": _trend_last_n_months(apps_qs, months=6),
    }

    health = _health_score(
        incidents_open=incidents_open,
        incidents_critical=incidents_critical,
        certs_expiring=certs_expiring,
        certs_expired=certs_expired,
        domains_expiring=domains_expiring,
        contracts_expiring=contracts_expiring,
    )

    status_breakdown = [
        {
            "key": key,
            "label": label,
            "count": count,
            "pct": _pct(count, apps_total),
        }
        for key, label, count in zip(
            apps_by_status_chart["keys"],
            apps_by_status_chart["labels"],
            apps_by_status_chart["values"],
            strict=True,
        )
        if count > 0 or key in {"production", "project"}
    ]

    return {
        "users_total": User.objects.count(),
        "apps_total": apps_total,
        "apps_production": apps_production,
        "apps_critical": apps_critical,
        "apps_production_pct": _pct(apps_production, apps_total),
        "techs_total": techs_total,
        "servers_total": servers_total,
        "envs_total": envs_total,
        "certs_total": certs_total,
        "certs_expiring": certs_expiring,
        "certs_expired": certs_expired,
        "certs_valid": certs_valid,
        "domains_total": domains_total,
        "domains_expiring": domains_expiring,
        "contracts_total": contracts_total,
        "contracts_expiring": contracts_expiring,
        "expiry_pressure": expiry_pressure,
        "vendors_total": vendors_total,
        "documents_total": documents_total,
        "incidents_open": incidents_open,
        "incidents_critical": incidents_critical,
        "dependencies_total": dependencies_total,
        "notifications_unread": unread,
        "health": health,
        "status_breakdown": status_breakdown,
        "upcoming_expiries": _upcoming_expiries(today=today),
        "documents_by_category": documents_by_category,
        "incidents_by_status": incidents_by_status,
        "apps_by_criticality": apps_by_criticality,
        "charts": charts,
    }
