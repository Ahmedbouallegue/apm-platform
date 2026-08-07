from django.db.models import Count, Q, QuerySet

from apps.vendors.models import Vendor


def vendor_list(
    *,
    search: str | None = None,
    vendor_type: str | None = None,
    is_active: bool | None = None,
    include_deleted: bool = False,
) -> QuerySet[Vendor]:
    qs = Vendor.objects.annotate(
        contract_count=Count("contracts", filter=Q(contracts__is_deleted=False))
    )
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(contact_name__icontains=search)
            | Q(contact_email__icontains=search)
            | Q(notes__icontains=search)
        )
    if vendor_type:
        qs = qs.filter(vendor_type=vendor_type)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs.order_by("name")
