from django.contrib import admin

from apps.environments.models import Environment


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "application",
        "env_type",
        "server",
        "url",
        "ip_address",
        "hosting_provider",
        "docker",
        "kubernetes",
        "is_active",
    )
    list_filter = ("env_type", "is_active", "docker", "kubernetes", "hosting_provider")
    search_fields = ("name", "url", "ip_address", "application__name", "os")
    autocomplete_fields = ("application", "server")
