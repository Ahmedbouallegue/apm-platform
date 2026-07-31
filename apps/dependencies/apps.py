from django.apps import AppConfig


class DependenciesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dependencies"
    label = "dependencies"
    verbose_name = "Dépendances applicatives"
