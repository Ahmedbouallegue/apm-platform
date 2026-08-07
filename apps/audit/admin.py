from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "occurred_at",
        "action",
        "entity",
        "entity_id",
        "user",
        "ip_address",
    )
    list_filter = ("action", "entity")
    search_fields = ("action", "entity", "entity_id", "details", "user__username")
    raw_id_fields = ("user",)
    readonly_fields = (
        "action",
        "entity",
        "entity_id",
        "details",
        "occurred_at",
        "user",
        "ip_address",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
