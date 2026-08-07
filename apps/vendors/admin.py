from django.contrib import admin

from apps.vendors.models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor_type", "contact_email", "is_active", "updated_at")
    list_filter = ("vendor_type", "is_active", "is_deleted")
    search_fields = ("name", "contact_name", "contact_email", "notes")
