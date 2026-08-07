from django.contrib import admin

from apps.notifications.models import Notification, PlatformSettings


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "notification_type",
        "status",
        "user",
        "sent_at",
    )
    list_filter = ("notification_type", "status")
    search_fields = ("title", "message", "user__username")
    raw_id_fields = ("user",)


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "alert_days_60",
        "alert_days_30",
        "alert_on_expiry",
        "alert_cooldown_days",
        "updated_at",
    )

    def has_add_permission(self, request):
        return not PlatformSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
