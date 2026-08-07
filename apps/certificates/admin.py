from django.contrib import admin

from apps.certificates.models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        "common_name",
        "certificate_type",
        "status",
        "issuer",
        "expires_at",
        "is_active",
    )
    list_filter = ("certificate_type", "status", "is_active", "is_deleted", "auto_renew")
    search_fields = ("common_name", "san_domains", "issuer", "notes")
    raw_id_fields = ("application", "environment", "domain")
