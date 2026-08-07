from django.db.models import Q, QuerySet

from apps.domains.models import Domain


def domain_list(
    *,
    search: str | None = None,
    status: str | None = None,
    application_id: int | None = None,
    is_active: bool | None = None,
    include_deleted: bool = False,
) -> QuerySet[Domain]:
    qs = Domain.objects.select_related("application", "environment")
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    if search:
        qs = qs.filter(
            Q(fqdn__icontains=search)
            | Q(registrar__icontains=search)
            | Q(dns_provider__icontains=search)
            | Q(notes__icontains=search)
        )
    if status:
        qs = qs.filter(status=status)
    if application_id:
        qs = qs.filter(application_id=application_id)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs.order_by("fqdn")
