from django.contrib import admin

from apps.incidents.models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "application",
        "impact",
        "status",
        "occurred_at",
        "reported_by",
    )
    list_filter = ("impact", "status", "is_deleted")
    search_fields = ("title", "description", "root_cause", "solution")
    raw_id_fields = ("application", "reported_by")
