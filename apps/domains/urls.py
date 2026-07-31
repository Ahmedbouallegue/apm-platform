from django.urls import path

from apps.domains.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="domains-health"),
]
