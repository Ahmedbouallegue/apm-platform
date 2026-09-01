"""
Context Builder — Construit un snapshot structuré du patrimoine applicatif
pour le Chatbot IA. Interroge directement PostgreSQL (pas de vecteurs).
"""
from __future__ import annotations

import json
from datetime import date, timedelta

from django.db.models import Count, Sum


def build_context(user) -> str:
    """
    Retourne un contexte JSON structuré décrivant l'état courant de la plateforme.
    Ce contexte est injecté dans le prompt Gemini.
    """
    # Import ici pour éviter les imports circulaires au niveau module
    from apps.applications.models import Application
    from apps.certificates.models import Certificate
    from apps.contracts.models import Contract
    from apps.incidents.models import Incident
    from apps.servers.models import Server
    from apps.vendors.models import Vendor

    today = date.today()
    in_30 = today + timedelta(days=30)
    in_60 = today + timedelta(days=60)
    last_30 = today - timedelta(days=30)

    # ---------- Applications ----------
    apps_qs = Application.objects.filter(is_deleted=False)
    apps_by_status = dict(
        apps_qs.values_list("status").annotate(n=Count("id")).values_list("status", "n")
    )
    apps_by_criticality = dict(
        apps_qs.values_list("criticality")
        .annotate(n=Count("id"))
        .values_list("criticality", "n")
    )
    critical_apps = list(
        apps_qs.filter(criticality="critical", status="production").values(
            "name", "business_unit", "user_count"
        )[:10]
    )

    # ---------- Certificats SSL ----------
    certs_qs = Certificate.objects.filter(is_deleted=False, is_active=True)
    expiring_soon = list(
        certs_qs.filter(expires_at__lte=in_30, expires_at__gte=today)
        .select_related("application")
        .values("common_name", "expires_at", "application__name", "status")[:10]
    )
    already_expired = list(
        certs_qs.filter(expires_at__lt=today)
        .select_related("application")
        .values("common_name", "expires_at", "application__name")[:10]
    )

    # ---------- Contrats ----------
    contracts_qs = Contract.objects.filter(is_deleted=False, is_active=True)
    expiring_contracts = list(
        contracts_qs.filter(end_date__lte=in_60, end_date__gte=today)
        .select_related("vendor", "application")
        .values("reference", "title", "end_date", "vendor__name", "application__name", "annual_cost", "currency")[:10]
    )
    total_cost = contracts_qs.aggregate(total=Sum("annual_cost"))["total"]

    # ---------- Incidents ----------
    incidents_qs = Incident.objects.filter(is_deleted=False)
    open_incidents = list(
        incidents_qs.filter(status__in=["ouvert", "en_cours"])
        .select_related("application")
        .values("title", "impact", "status", "application__name", "occurred_at")[:10]
    )
    recent_resolved = incidents_qs.filter(
        status="resolu", occurred_at__date__gte=last_30
    ).count()

    # ---------- Serveurs ----------
    try:
        from apps.servers.models import Server

        servers_total = Server.objects.filter(is_deleted=False).count()
        servers_by_status = dict(
            Server.objects.filter(is_deleted=False)
            .values_list("status")
            .annotate(n=Count("id"))
            .values_list("status", "n")
        )
    except Exception:
        servers_total = "N/A"
        servers_by_status = {}

    # ---------- Fournisseurs ----------
    vendors_count = Vendor.objects.filter(is_deleted=False).count()

    # ---------- Assemblage ----------
    ctx = {
        "date_today": str(today),
        "applications": {
            "total": apps_qs.count(),
            "by_status": apps_by_status,
            "by_criticality": apps_by_criticality,
            "critical_in_production": critical_apps,
        },
        "ssl_certificates": {
            "expiring_in_30_days": _serialize_dates(expiring_soon),
            "already_expired": _serialize_dates(already_expired),
        },
        "contracts": {
            "expiring_in_60_days": _serialize_dates(expiring_contracts),
            "total_annual_cost_TND": float(total_cost) if total_cost else 0,
            "active_count": contracts_qs.count(),
        },
        "incidents": {
            "open_or_in_progress": _serialize_dates(open_incidents),
            "resolved_last_30_days": recent_resolved,
        },
        "servers": {
            "total": servers_total,
            "by_status": servers_by_status,
        },
        "vendors": {
            "total": vendors_count,
        },
    }

    return json.dumps(ctx, ensure_ascii=False, default=str, indent=2)


def _serialize_dates(lst: list[dict]) -> list[dict]:
    """Convertit les objets date/datetime en strings pour JSON."""
    result = []
    for item in lst:
        result.append({k: str(v) if hasattr(v, "isoformat") else v for k, v in item.items()})
    return result
