from django.urls import path

from apps.dependencies.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="dependencies-health"),
]
