from django.db.models import Q, QuerySet

from apps.contracts.models import Contract


def contract_list(
    *,
    search: str | None = None,
    contract_type: str | None = None,
    status: str | None = None,
    vendor_id: int | None = None,
    is_active: bool | None = None,
    include_deleted: bool = False,
) -> QuerySet[Contract]:
    qs = Contract.objects.select_related("vendor", "application", "owner")
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    if search:
        qs = qs.filter(
            Q(reference__icontains=search)
            | Q(title__icontains=search)
            | Q(vendor__name__icontains=search)
            | Q(sla_level__icontains=search)
            | Q(notes__icontains=search)
        )
    if contract_type:
        qs = qs.filter(contract_type=contract_type)
    if status:
        qs = qs.filter(status=status)
    if vendor_id:
        qs = qs.filter(vendor_id=vendor_id)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs.order_by("-end_date", "reference")
