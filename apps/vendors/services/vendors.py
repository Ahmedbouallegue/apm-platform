from django.db import transaction
from django.utils import timezone

from apps.vendors.models import Vendor


@transaction.atomic
def vendor_create(*, data: dict) -> Vendor:
    vendor = Vendor(**data)
    vendor.full_clean()
    vendor.save()
    return vendor


@transaction.atomic
def vendor_update(*, vendor: Vendor, data: dict) -> Vendor:
    for field, value in data.items():
        setattr(vendor, field, value)
    vendor.full_clean()
    vendor.save()
    return vendor


@transaction.atomic
def vendor_soft_delete(*, vendor: Vendor) -> Vendor:
    vendor.is_deleted = True
    vendor.deleted_at = timezone.now()
    vendor.is_active = False
    vendor.save(update_fields=["is_deleted", "deleted_at", "is_active", "updated_at"])
    return vendor
