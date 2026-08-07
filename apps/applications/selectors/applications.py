from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

from apps.applications.models import Application

User = get_user_model()


def application_list(
    *,
    search: str | None = None,
    status: str | None = None,
    criticality: str | None = None,
    business_unit: str | None = None,
    owner_id: int | None = None,
    include_deleted: bool = False,
) -> QuerySet[Application]:
    qs = Application.objects.select_related("owner")
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(business_unit__icontains=search)
        )
    if status:
        qs = qs.filter(status=status)
    if criticality:
        qs = qs.filter(criticality=criticality)
    if business_unit:
        qs = qs.filter(business_unit__icontains=business_unit)
    if owner_id:
        qs = qs.filter(owner_id=owner_id)
    return qs.order_by("name")


def application_get(*, application_id: int, include_deleted: bool = False) -> Application:
    qs = Application.objects.select_related("owner").prefetch_related("technologies")
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    return qs.get(pk=application_id)
