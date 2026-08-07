from django.contrib import admin

from apps.contracts.models import Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "title",
        "vendor",
        "contract_type",
        "status",
        "end_date",
        "is_active",
    )
    list_filter = ("contract_type", "status", "is_active", "is_deleted")
    search_fields = ("reference", "title", "vendor__name", "notes")
    raw_id_fields = ("vendor", "application", "owner")
