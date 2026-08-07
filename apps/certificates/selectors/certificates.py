from django.db.models import Q, QuerySet

from apps.certificates.models import Certificate


def certificate_list(
    *,
    search: str | None = None,
    status: str | None = None,
    certificate_type: str | None = None,
    application_id: int | None = None,
    is_active: bool | None = None,
    include_deleted: bool = False,
    with_related: bool = False,
) -> QuerySet[Certificate]:
    qs = Certificate.objects.all()
    if with_related:
        qs = qs.select_related("application", "environment", "domain")
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    if search:
        qs = qs.filter(
            Q(common_name__icontains=search)
            | Q(san_domains__icontains=search)
            | Q(issuer__icontains=search)
            | Q(notes__icontains=search)
        )
    if status:
        qs = qs.filter(status=status)
    if certificate_type:
        qs = qs.filter(certificate_type=certificate_type)
    if application_id:
        qs = qs.filter(application_id=application_id)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs.order_by("expires_at", "common_name")
