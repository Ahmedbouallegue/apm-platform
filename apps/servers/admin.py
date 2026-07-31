from django.contrib import admin

from apps.servers.models import Server


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "ip_address",
        "server_type",
        "os",
        "cpu",
        "ram",
        "datacenter",
        "is_active",
        "is_deleted",
    )
    list_filter = ("server_type", "is_active", "is_deleted", "datacenter")
    search_fields = ("name", "ip_address", "os", "datacenter", "notes")
