from django.contrib import admin

from apps.dependencies.models import Dependency


@admin.register(Dependency)
class DependencyAdmin(admin.ModelAdmin):
    list_display = (
        "source_application",
        "dependency_type",
        "target_application",
        "target_external",
        "is_active",
    )
    list_filter = ("dependency_type", "is_active", "is_deleted")
    search_fields = (
        "description",
        "target_external",
        "source_application__name",
        "target_application__name",
    )
    raw_id_fields = ("source_application", "target_application")
