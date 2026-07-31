from django.contrib import admin

from apps.applications.models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "status",
        "criticality",
        "business_unit",
        "owner",
        "user_count",
        "go_live_date",
        "is_deleted",
    )
    list_filter = ("status", "criticality", "business_unit", "is_deleted")
    search_fields = ("name", "description", "business_unit")
    autocomplete_fields = ("owner",)
    filter_horizontal = ("technologies",)
    date_hierarchy = "go_live_date"
