from django.contrib import admin

from apps.technologies.models import Technology


@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ("name", "tech_type", "version", "created_at")
    list_filter = ("tech_type",)
    search_fields = ("name", "version", "description")
