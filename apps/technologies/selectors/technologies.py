from django.db.models import Count, Q, QuerySet

from apps.technologies.models import Technology


def technology_list(
    *,
    search: str | None = None,
    tech_type: str | None = None,
) -> QuerySet[Technology]:
    qs = Technology.objects.annotate(app_count=Count("applications")).all()
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(version__icontains=search)
            | Q(description__icontains=search)
        )
    if tech_type:
        qs = qs.filter(tech_type=tech_type)
    return qs.order_by("name", "version")


def technology_get(*, technology_id: int) -> Technology:
    return Technology.objects.annotate(app_count=Count("applications")).get(pk=technology_id)
