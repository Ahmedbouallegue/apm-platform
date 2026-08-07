from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q, QuerySet
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.applications.models import Application
from apps.certificates.models import Certificate
from apps.contracts.models import Contract
from apps.dependencies.models import Dependency
from apps.documents.models import Document
from apps.domains.models import Domain
from apps.incidents.models import Incident
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

DASHBOARD_STATS_CACHE_KEY = "dashboard:stats:v1"


def invalidate_dashboard_stats() -> None:
    cache.delete(DASHBOARD_STATS_CACHE_KEY)


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
    # Datetime lower bound keeps indexes usable (avoids __date__ cast).
    start_dt = timezone.make_aware(datetime.combine(start, time.min))
    filter_kwargs = {f"{date_field}__gte": start_dt}
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
    d30 = today + timedelta(days=30)
    d90 = today + timedelta(days=90)
    row = certs.aggregate(
        expired=Count("id", filter=Q(expires_at__lt=today)),
        within_30=Count("id", filter=Q(expires_at__gte=today, expires_at__lte=d30)),
        within_90=Count("id", filter=Q(expires_at__gt=d30, expires_at__lte=d90)),
        later=Count("id", filter=Q(expires_at__gt=d90)),
    )
    return {
        "labels": ["Expirés", "≤ 30 jours", "31–90 jours", "> 90 jours"],
        "values": [
            int(row["expired"] or 0),
            int(row["within_30"] or 0),
            int(row["within_90"] or 0),
            int(row["later"] or 0),
        ],
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

    for cert in (
        Certificate.objects.filter(
            is_deleted=False,
            is_active=True,
            expires_at__gte=today,
            expires_at__lte=horizon,
        )
        .exclude(status=Certificate.Status.REVOKED)
        .order_by("expires_at")[:limit]
    ):
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

    for contract in (
        Contract.objects.filter(
            is_deleted=False,
            is_active=True,
            end_date__gte=today,
            end_date__lte=horizon,
        )
        .exclude(status=Contract.Status.TERMINATED)
        .order_by("end_date")[:limit]
    ):
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


def _compute_dashboard_stats() -> dict:
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

    apps_agg = apps_qs.aggregate(
        apps_total=Count("id"),
        apps_production=Count("id", filter=Q(status=Application.Status.PRODUCTION)),
        apps_critical=Count(
            "id",
            filter=Q(
                criticality__in=[
                    Application.Criticality.CRITICAL,
                    Application.Criticality.HIGH,
                ]
            ),
        ),
    )
    apps_total = int(apps_agg["apps_total"] or 0)
    apps_production = int(apps_agg["apps_production"] or 0)
    apps_critical = int(apps_agg["apps_critical"] or 0)

    certs_agg = certs.aggregate(
        certs_total=Count("id"),
        certs_expiring=Count(
            "id",
            filter=Q(
                expires_at__lte=soon,
                expires_at__gte=today,
                status__in=[Certificate.Status.VALID, Certificate.Status.EXPIRING],
            ),
        ),
        certs_expired=Count("id", filter=Q(expires_at__lt=today)),
        certs_valid=Count(
            "id",
            filter=Q(status=Certificate.Status.VALID, expires_at__gt=soon),
        ),
    )
    domains_agg = domains.aggregate(
        domains_total=Count("id"),
        domains_expiring=Count(
            "id",
            filter=Q(
                expires_at__isnull=False,
                expires_at__lte=soon,
                expires_at__gte=today,
            ),
        ),
    )
    contracts_agg = contracts.aggregate(
        contracts_total=Count("id"),
        contracts_expiring=Count(
            "id",
            filter=Q(
                end_date__lte=soon,
                end_date__gte=today,
                status__in=[Contract.Status.ACTIVE, Contract.Status.EXPIRING],
            ),
        ),
    )
    incidents_agg = open_incidents.aggregate(
        incidents_open=Count("id"),
        incidents_critical=Count("id", filter=Q(impact=Incident.Impact.CRITICAL)),
    )

    techs_total = Technology.objects.count()
    vendors_total = Vendor.objects.filter(is_deleted=False).count()
    documents_total = docs_qs.count()
    dependencies_total = Dependency.objects.filter(is_deleted=False).count()
    servers_total = Server.objects.filter(is_deleted=False).count()
    envs_total = Environment.objects.count()
    users_total = User.objects.count()

    certs_total = int(certs_agg["certs_total"] or 0)
    certs_expiring = int(certs_agg["certs_expiring"] or 0)
    certs_expired = int(certs_agg["certs_expired"] or 0)
    certs_valid = int(certs_agg["certs_valid"] or 0)
    domains_total = int(domains_agg["domains_total"] or 0)
    domains_expiring = int(domains_agg["domains_expiring"] or 0)
    contracts_total = int(contracts_agg["contracts_total"] or 0)
    contracts_expiring = int(contracts_agg["contracts_expiring"] or 0)
    incidents_open = int(incidents_agg["incidents_open"] or 0)
    incidents_critical = int(incidents_agg["incidents_critical"] or 0)
    expiry_pressure = certs_expiring + domains_expiring + contracts_expiring

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
        "users_total": users_total,
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
        "health": health,
        "status_breakdown": status_breakdown,
        "upcoming_expiries": _upcoming_expiries(today=today),
        "documents_by_category": documents_by_category,
        "incidents_by_status": incidents_by_status,
        "apps_by_criticality": apps_by_criticality,
        "charts": charts,
    }


def dashboard_stats(*, user=None) -> dict:
    ttl = int(getattr(settings, "DASHBOARD_STATS_CACHE_TTL", 120))
    if ttl > 0:
        stats = cache.get(DASHBOARD_STATS_CACHE_KEY)
        if stats is None:
            stats = _compute_dashboard_stats()
            cache.set(DASHBOARD_STATS_CACHE_KEY, stats, ttl)
        else:
            # Shallow copy so per-request unread does not mutate the cache entry.
            stats = {**stats}
    else:
        stats = _compute_dashboard_stats()

    unread = 0
    if user is not None and getattr(user, "is_authenticated", False):
        from apps.notifications.services.badge import unread_count_for_user

        unread = unread_count_for_user(user.pk)
    stats["notifications_unread"] = unread
    return stats
