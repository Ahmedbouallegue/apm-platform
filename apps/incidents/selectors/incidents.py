from django.db.models import Q, QuerySet

from apps.incidents.models import Incident


def incident_list(
    *,
    search: str | None = None,
    status: str | None = None,
    impact: str | None = None,
    application_id: int | None = None,
    include_deleted: bool = False,
) -> QuerySet[Incident]:
    qs = Incident.objects.select_related("application", "reported_by")
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    if search:
        qs = qs.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(root_cause__icontains=search)
            | Q(solution__icontains=search)
            | Q(application__name__icontains=search)
        )
    if status:
        qs = qs.filter(status=status)
    if impact:
        qs = qs.filter(impact=impact)
    if application_id:
        qs = qs.filter(application_id=application_id)
    return qs.order_by("-occurred_at", "title")
