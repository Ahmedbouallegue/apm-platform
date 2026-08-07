from django.contrib import admin

from apps.domains.models import Domain


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("fqdn", "status", "registrar", "expires_at", "is_primary", "auto_renew", "is_active")
    list_filter = ("status", "is_primary", "is_active", "is_deleted")
    search_fields = ("fqdn", "registrar", "dns_provider", "notes")
    raw_id_fields = ("application", "environment")
